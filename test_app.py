import json
import os
import tempfile
import threading
import unittest
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer

class AppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        os.environ['DATABASE_PATH']=cls.tmp.name+'/test.sqlite3'
        os.environ['QUIET']='1'
        import app
        cls.app=app
        app.init_db()
        cls.http=ThreadingHTTPServer(('127.0.0.1',0),app.Handler)
        cls.port=cls.http.server_address[1]
        cls.thread=threading.Thread(target=cls.http.serve_forever,daemon=True)
        cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown();cls.http.server_close();cls.thread.join();cls.tmp.cleanup()
    def req(self,method,path,body=None,user=1):
        data=json.dumps(body).encode() if body is not None else None
        r=urllib.request.Request(f'http://127.0.0.1:{self.port}/api{path}',data=data,method=method,headers={'Content-Type':'application/json','X-Demo-User':str(user)})
        try:
            with urllib.request.urlopen(r) as f:return f.status,json.load(f)
        except urllib.error.HTTPError as e:return e.code,json.load(e)
    def test_create_format_share_edit_and_permissions(self):
        code,body=self.req('POST','/documents',{'title':'Project brief','content':'<h1>Welcome</h1><p><strong>Bold</strong> text</p><script>alert(1)</script>'})
        self.assertEqual(code,201); doc=body['document'];ident=doc['id']
        self.assertIn('<strong>Bold</strong>',doc['content']);self.assertNotIn('<script>',doc['content']);self.assertNotIn('alert(1)',doc['content'])
        self.assertEqual(self.req('GET',f'/documents/{ident}',user=2)[0],404)
        self.assertEqual(self.req('POST',f'/documents/{ident}/share',{'user_id':2},user=2)[0],404)
        code,body=self.req('POST',f'/documents/{ident}/share',{'user_id':2})
        self.assertEqual(code,200);self.assertEqual(len(body['document']['shared_with']),1)
        self.assertFalse(self.req('GET',f'/documents/{ident}',user=2)[1]['document']['is_owner'])
        code,body=self.req('PATCH',f'/documents/{ident}',{'version':doc['version'],'content':'<p>Updated by Sam</p>'},user=2)
        self.assertEqual(code,200);self.assertEqual(body['document']['version'],2)
        self.assertEqual(self.req('PATCH',f'/documents/{ident}',{'version':doc['version'],'title':'Stale'},user=1)[0],409)
        self.assertEqual(self.req('DELETE',f'/documents/{ident}',user=2)[0],403)
        self.assertEqual(self.req('DELETE',f'/documents/{ident}/share/2')[0],200)
        self.assertEqual(self.req('GET',f'/documents/{ident}',user=2)[0],404)
    def test_import_validation_and_escaping(self):
        code,body=self.req('POST','/import',{'filename':'plan.md','text':'# Team plan\n- First\n- Second'})
        self.assertEqual(code,201);self.assertIn('<h1>Team plan</h1>',body['document']['content']);self.assertIn('<ul>',body['document']['content'])
        self.assertEqual(self.req('POST','/import',{'filename':'bad.exe','text':'hello'})[0],400)
        code,body=self.req('POST','/import',{'filename':'test.txt','text':'<script>not executed</script>'})
        self.assertEqual(code,201);self.assertIn('&lt;script&gt;',body['document']['content'])
        self.assertEqual(self.req('POST','/documents',{'title':''})[0],400)
    def test_xss_strips_attributes(self):
        clean=self.app.safe_content('<p onclick="evil()">Hey<img src=x onerror="evil()"><b style="color:red">Bold</b></p>')
        self.assertEqual(clean,'<p>Hey<b>Bold</b></p>')

if __name__=='__main__': unittest.main()
