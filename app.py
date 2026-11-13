"""Ajaia Docs: dependency-free collaborative document demo."""
import html
import json
import mimetypes
import os
import re
import sqlite3
from datetime import datetime, timezone
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).parent
DB_PATH = Path(os.environ.get('DATABASE_PATH', str(ROOT / 'data' / 'docs.sqlite3')))
MAX_JSON_BYTES = 1_500_000
MAX_UPLOAD_BYTES = 500_000
USERS = {1: {'id': 1, 'name': 'Alex Morgan', 'email': 'alex@ajaia.demo'}, 2: {'id': 2, 'name': 'Sam Rivera', 'email': 'sam@ajaia.demo'}}

@contextmanager
def connection():
    db = sqlite3.connect(DB_PATH, timeout=10)
    try:
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('PRAGMA busy_timeout=10000')
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connection() as db:
        db.execute('PRAGMA journal_mode=WAL')
        db.executescript('''
            CREATE TABLE IF NOT EXISTS docs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL DEFAULT '',
                owner_id INTEGER NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS shares (
                doc_id INTEGER NOT NULL REFERENCES docs(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL,
                PRIMARY KEY (doc_id, user_id)
            );
        ''')

def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')

def safe_content(value):
    """Conservative HTML allowlist; all scriptable attributes stripped."""
    from html.parser import HTMLParser
    class Sanitizer(HTMLParser):
        ALLOWED = {'p','div','br','strong','b','em','i','u','h1','h2','h3','ul','ol','li','blockquote','span'}
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.parts=[]; self.stack=[]; self.blocked=0
        def handle_starttag(self, tag, attrs):
            if tag in ('script','style','iframe','svg','math','object','template'):
                self.blocked+=1; self.stack.append((tag,False)); return
            if self.blocked:
                self.stack.append((tag,False)); return
            allowed=tag in self.ALLOWED
            self.stack.append((tag,allowed))
            if allowed: self.parts.append('<'+tag+'>')
        def handle_startendtag(self, tag, attrs):
            if not self.blocked and tag=='br': self.parts.append('<br>')
        def handle_endtag(self, tag):
            if not self.stack: return
            # Close nearest corresponding open tag only; prevents unbalanced generated HTML.
            idx=next((i for i in range(len(self.stack)-1,-1,-1) if self.stack[i][0]==tag),None)
            if idx is None: return
            for opened,allowed in reversed(self.stack[idx:]):
                if opened in ('script','style','iframe','svg','math','object','template'): self.blocked=max(0,self.blocked-1)
                if allowed and opened!='br': self.parts.append('</'+opened+'>')
            self.stack=self.stack[:idx]
        def handle_data(self,data):
            if not self.blocked: self.parts.append(html.escape(data))
        def close(self):
            super().close()
            for tag,allowed in reversed(self.stack):
                if allowed and tag!='br': self.parts.append('</'+tag+'>')
    parser=Sanitizer(); parser.feed(value); parser.close()
    return ''.join(parser.parts)

def import_text(filename, body):
    if not isinstance(filename, str) or not filename.lower().endswith(('.txt','.md')): raise ValueError('Only .txt and .md files are supported')
    if len(body.encode('utf-8')) > MAX_UPLOAD_BYTES: raise ValueError('File is too large (maximum 500 KB)')
    title=Path(filename).stem.strip()[:100] or 'Imported document'
    if filename.lower().endswith('.txt'):
        paragraphs=body.replace('\r\n','\n').split('\n\n')
        content=''.join('<p>'+html.escape(p).replace('\n','<br>')+'</p>' for p in paragraphs)
    else:
        out=[]; listing=None
        for line in body.replace('\r\n','\n').split('\n'):
            if not line.strip():
                if listing: out.append('</'+listing+'>'); listing=None
                continue
            heading=re.match(r'^(#{1,3})\s+(.+)$',line)
            bullet=re.match(r'^\s*[-*]\s+(.+)$',line)
            numbered=re.match(r'^\s*\d+\.\s+(.+)$',line)
            if heading:
                if listing: out.append('</'+listing+'>'); listing=None
                tag='h'+str(len(heading.group(1))); out.append(f'<{tag}>{html.escape(heading.group(2))}</{tag}>')
            elif bullet or numbered:
                target='ul' if bullet else 'ol'
                if listing!=target:
                    if listing: out.append('</'+listing+'>')
                    out.append('<'+target+'>'); listing=target
                out.append('<li>'+html.escape((bullet or numbered).group(1))+'</li>')
            else:
                if listing: out.append('</'+listing+'>'); listing=None
                out.append('<p>'+html.escape(line)+'</p>')
        if listing: out.append('</'+listing+'>')
        content=''.join(out)
    return title, content

def serialize(db, doc, user):
    doc=dict(doc)
    doc['is_owner']=doc['owner_id']==user
    doc['owner_name']=USERS[doc['owner_id']]['name']
    doc['shared_with']=[dict(USERS[r['user_id']]) for r in db.execute('SELECT user_id FROM shares WHERE doc_id=?',(doc['id'],))]
    return doc

class APIError(Exception):
    def __init__(self, status, message): self.status=status; self.message=message

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        if os.environ.get('QUIET') != '1': super().log_message(fmt,*args)
    def respond(self, code, data):
        raw=json.dumps(data).encode('utf-8')
        self.send_response(code); self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Cache-Control','no-store'); self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def json_body(self):
        try: length=int(self.headers.get('Content-Length','0'))
        except ValueError: raise APIError(400,'Invalid content length')
        if length<1 or length>MAX_JSON_BYTES: raise APIError(413,'Request is empty or too large')
        try: value=json.loads(self.rfile.read(length).decode('utf-8'))
        except (UnicodeError,json.JSONDecodeError): raise APIError(400,'Invalid JSON body')
        if not isinstance(value,dict): raise APIError(400,'Expected JSON object')
        return value
    def user(self):
        try: uid=int(self.headers.get('X-Demo-User','1'))
        except ValueError: raise APIError(400,'Invalid demo user')
        if uid not in USERS: raise APIError(401,'Unknown demo user')
        return uid
    def doc(self, db, doc_id, user):
        doc=db.execute('''SELECT d.* FROM docs d WHERE d.id=? AND
            (d.owner_id=? OR EXISTS (SELECT 1 FROM shares s WHERE s.doc_id=d.id AND s.user_id=?))''',(doc_id,user,user)).fetchone()
        if not doc: raise APIError(404,'Document not found or not shared with this user')
        return doc
    def handle_api(self, method):
        path=urlparse(self.path).path; user=self.user()
        parts=path.strip('/').split('/')
        with connection() as db:
            if path=='/api/users' and method=='GET': return 200, {'users':list(USERS.values()),'current_user':user}
            if path=='/api/documents' and method=='GET':
                docs=db.execute('''SELECT DISTINCT d.* FROM docs d LEFT JOIN shares s ON s.doc_id=d.id
                      WHERE d.owner_id=? OR s.user_id=? ORDER BY d.updated_at DESC,d.id DESC''',(user,user)).fetchall()
                return 200, {'documents':[serialize(db,d,user) for d in docs]}
            if path=='/api/documents' and method=='POST':
                data=self.json_body(); title=data.get('title','Untitled document')
                if not isinstance(title,str) or not title.strip() or len(title)>100: raise APIError(400,'Title must be 1–100 characters')
                content=data.get('content','')
                if not isinstance(content,str) or len(content)>400_000: raise APIError(400,'Document content must be under 400,000 characters')
                stamp=now()
                cur=db.execute('INSERT INTO docs (title,content,owner_id,created_at,updated_at) VALUES (?,?,?,?,?)',(title.strip(),safe_content(content),user,stamp,stamp))
                doc=db.execute('SELECT * FROM docs WHERE id=?',(cur.lastrowid,)).fetchone()
                return 201, {'document':serialize(db,doc,user)}
            if path=='/api/import' and method=='POST':
                data=self.json_body(); body=data.get('text'); filename=data.get('filename')
                if not isinstance(body,str): raise APIError(400,'File text is required')
                try: title,content=import_text(filename,body)
                except ValueError as error: raise APIError(400,str(error))
                stamp=now(); cur=db.execute('INSERT INTO docs (title,content,owner_id,created_at,updated_at) VALUES (?,?,?,?,?)',(title,content,user,stamp,stamp))
                return 201, {'document':serialize(db,db.execute('SELECT * FROM docs WHERE id=?',(cur.lastrowid,)).fetchone(),user)}
            if len(parts)>=3 and parts[:2]==['api','documents'] and parts[2].isdigit():
                doc_id=int(parts[2]); doc=self.doc(db,doc_id,user)
                if len(parts)==3 and method=='GET': return 200, {'document':serialize(db,doc,user)}
                if len(parts)==3 and method=='PATCH':
                    data=self.json_body(); version=data.get('version')
                    if type(version) is not int: raise APIError(400,'Version is required')
                    changes={}
                    if 'title' in data:
                        title=data['title']
                        if not isinstance(title,str) or not title.strip() or len(title)>100: raise APIError(400,'Title must be 1–100 characters')
                        changes['title']=title.strip()
                    if 'content' in data:
                        content=data['content']
                        if not isinstance(content,str) or len(content)>400_000: raise APIError(400,'Document content must be under 400,000 characters')
                        changes['content']=safe_content(content)
                    if not changes: raise APIError(400,'No changes provided')
                    changes['version']=version+1; changes['updated_at']=now()
                    columns=', '.join(f'{name}=?' for name in changes)
                    cur=db.execute(f'UPDATE docs SET {columns} WHERE id=? AND version=?',(*changes.values(),doc_id,version))
                    if cur.rowcount!=1: raise APIError(409,'This document was updated elsewhere. Refresh before saving again.')
                    return 200, {'document':serialize(db,db.execute('SELECT * FROM docs WHERE id=?',(doc_id,)).fetchone(),user)}
                if len(parts)==3 and method=='DELETE':
                    if doc['owner_id']!=user: raise APIError(403,'Only the owner can delete a document')
                    db.execute('DELETE FROM docs WHERE id=?',(doc_id,)); return 200, {'ok':True}
                if len(parts)==4 and parts[3]=='share' and method=='POST':
                    if doc['owner_id']!=user: raise APIError(403,'Only the owner can share a document')
                    data=self.json_body(); target=data.get('user_id')
                    if type(target) is not int or target not in USERS or target==user: raise APIError(400,'Select another valid demo user')
                    db.execute('INSERT OR IGNORE INTO shares (doc_id,user_id) VALUES (?,?)',(doc_id,target))
                    return 200, {'document':serialize(db,db.execute('SELECT * FROM docs WHERE id=?',(doc_id,)).fetchone(),user)}
                if len(parts)==5 and parts[3]=='share' and parts[4].isdigit() and method=='DELETE':
                    if doc['owner_id']!=user: raise APIError(403,'Only the owner can remove sharing')
                    db.execute('DELETE FROM shares WHERE doc_id=? AND user_id=?',(doc_id,int(parts[4])))
                    return 200, {'document':serialize(db,db.execute('SELECT * FROM docs WHERE id=?',(doc_id,)).fetchone(),user)}
        raise APIError(404,'Endpoint not found')
    def route(self, method):
        path=urlparse(self.path).path
        if not path.startswith('/api/'):
            if method!='GET': return self.respond(405,{'error':'Method not allowed'})
            file=ROOT / ('index.html' if path=='/' else path.lstrip('/'))
            if file.parent!=ROOT or not file.is_file() or file.suffix not in ('.html','.css','.js','.svg'): return self.respond(404,{'error':'Not found'})
            raw=file.read_bytes(); ctype=mimetypes.guess_type(str(file))[0] or 'application/octet-stream'
            self.send_response(200); self.send_header('Content-Type',ctype+'; charset=utf-8'); self.send_header('Content-Length',str(len(raw))); self.send_header('X-Content-Type-Options','nosniff'); self.end_headers(); self.wfile.write(raw); return
        try: code,payload=self.handle_api(method); self.respond(code,payload)
        except APIError as exc: self.respond(exc.status,{'error':exc.message})
        except (sqlite3.Error, OSError) as exc:
            print('Server error:',repr(exc)); self.respond(500,{'error':'Internal server error'})
    def do_GET(self): self.route('GET')
    def do_POST(self): self.route('POST')
    def do_PATCH(self): self.route('PATCH')
    def do_DELETE(self): self.route('DELETE')

if __name__=='__main__':
    init_db(); port=int(os.environ.get('PORT','8000'))
    print(f'Ajaia Docs on http://localhost:{port}')
    ThreadingHTTPServer(('0.0.0.0',port),Handler).serve_forever()
