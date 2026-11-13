const $ = id => document.getElementById(id);
const state = { user: 1, docs: [], current: null, view: 'all', dirty: false, saving: false, timer: null, epoch: 0 };
const names = { 1: 'Alex Morgan', 2: 'Sam Rivera' };
const escapeHTML = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const formatDate = s => new Date(s).toLocaleDateString(undefined, { month:'short', day:'numeric', year:'numeric' });
function notify(message) { const el=$('toast'); el.textContent=message; el.hidden=false; clearTimeout(notify.timer); notify.timer=setTimeout(()=>el.hidden=true,3900); }
async function api(path, options={}) {
  let response;
  try { response=await fetch('/api'+path, { ...options, headers:{'Content-Type':'application/json','X-Demo-User':String(state.user), ...(options.headers||{})} }); }
  catch { throw new Error('Network connection failed. Check the server.'); }
  const data=await response.json(); if (!response.ok) throw new Error(data.error || 'Request failed'); return data;
}
async function loadDocs() {
  const { documents }=await api('/documents'); state.docs=documents; renderHome();
}
function renderHome() {
  const owned=state.docs.filter(d=>d.is_owner), shared=state.docs.filter(d=>!d.is_owner);
  $('allCount').textContent=state.docs.length; $('ownedCount').textContent=owned.length; $('sharedCount').textContent=shared.length;
  let list=state.view==='owned'?owned:state.view==='shared'?shared:state.docs;
  const label={ all:'All documents',owned:'My documents',shared:'Shared with me' }[state.view];
  $('breadcrumb').textContent=label;$('listTitle').textContent=label;$('docCount').textContent=`${list.length} document${list.length===1?'':'s'}`;
  $('greeting').innerHTML=`Good to see you, ${escapeHTML(names[state.user].split(' ')[0])} <span>✳</span>`;
  $('docGrid').innerHTML=list.map(d=>`<article class="doc-card" tabindex="0" role="button" data-id="${d.id}" aria-label="Open ${escapeHTML(d.title)}"><div class="doc-icon">▤</div><h3>${escapeHTML(d.title)}</h3><p>${d.is_owner?'Created by you':'Shared by '+escapeHTML(d.owner_name)}</p><div class="doc-bottom"><span>Edited ${formatDate(d.updated_at)}</span><span class="${d.is_owner?'owner-badge':'shared-badge'}">${d.is_owner?'Owned':'Shared'}</span></div></article>`).join('');
  $('empty').hidden=list.length>0;
  for (const el of document.querySelectorAll('.doc-card')) {
    el.addEventListener('click',()=>openDoc(Number(el.dataset.id)));
    el.addEventListener('keydown',e=>{if(e.key==='Enter')openDoc(Number(el.dataset.id));});
  }
  document.querySelectorAll('.nav').forEach(el=>el.classList.toggle('active',el.dataset.view===state.view));
}
function showHome(){ $('home').hidden=false;$('editorView').hidden=true;state.current=null;state.dirty=false;state.epoch++;$('breadcrumb').textContent='All documents'; }
async function openDoc(id) {
  try {
    await flush(); const {document:d}=await api('/documents/'+id); state.current=d; state.dirty=false;state.epoch++;
    $('home').hidden=true;$('editorView').hidden=false;$('docTitle').value=d.title;$('editor').innerHTML=d.content;
    $('docMeta').textContent=d.is_owner?'Owned by you':'Shared by '+d.owner_name;
    $('shareBtn').textContent=d.is_owner?'♧ Share':'♧ Access';$('deleteBtn').hidden=!d.is_owner;
    $('breadcrumb').textContent=d.title;setSaveState('All changes saved');updateWordCount();
  } catch (err) { notify(err.message); }
}
function setSaveState(s){$('saveState').textContent=s;$('status').textContent=s;}
function updateWordCount(){const text=$('editor').innerText.trim();$('wordCount').textContent=`${text?text.split(/\s+/).length:0} words`;}
function edit(){state.dirty=true;setSaveState('Unsaved changes');updateWordCount();clearTimeout(state.timer);state.timer=setTimeout(()=>saveDoc(),650);}
async function saveDoc(){
  if (!state.current||!state.dirty||state.saving)return;
  state.saving=true;clearTimeout(state.timer);
  const d=state.current, epoch=state.epoch, content=$('editor').innerHTML, title=$('docTitle').value.trim() || 'Untitled document';
  state.dirty=false;setSaveState('Saving…');
  try {
    const result=await api('/documents/'+d.id,{method:'PATCH',body:JSON.stringify({title,content,version:d.version})});
    if(epoch!==state.epoch)return;
    state.current=result.document;state.docs=state.docs.map(x=>x.id===d.id?result.document:x);
    $('breadcrumb').textContent=title;
    setSaveState(state.dirty?'Unsaved changes':'All changes saved');
  } catch(err){
    if(epoch!==state.epoch)return;
    state.dirty=true;setSaveState('Save failed');notify(err.message);
  } finally {
    state.saving=false;
    if(state.dirty&&epoch===state.epoch&&$('saveState').textContent!=='Save failed')state.timer=setTimeout(()=>saveDoc(),400);
  }
}
async function flush() {
  clearTimeout(state.timer);
  if(state.saving){for(let i=0;i<40&&state.saving;i++)await new Promise(r=>setTimeout(r,50));}
  if(state.dirty)await saveDoc();
  if(state.dirty)throw new Error('Please resolve the save error before leaving this document.');
}
async function createDoc(title='Untitled document',content=''){
  try {await flush();const {document:d}=await api('/documents',{method:'POST',body:JSON.stringify({title,content})});await loadDocs();await openDoc(d.id);$('editor').focus();}
  catch(err){notify(err.message);}
}
async function doImport(file) {
  if (!file)return;
  if(!/\.(txt|md)$/i.test(file.name)){notify('Only .txt and .md files are supported.');return;}
  if(file.size>500000){notify('Maximum import size is 500 KB.');return;}
  try {
    await flush();const text=await file.text();const {document:d}=await api('/import',{method:'POST',body:JSON.stringify({filename:file.name,text})});await loadDocs();await openDoc(d.id);notify('File imported as an editable document.');
  }catch(err){notify(err.message);}finally{$('fileUpload').value='';}
}
function renderShare(){
  const d=state.current;if(!d)return;
  $('modalOverlay').hidden=false;
  $('shareControls').hidden=!d.is_owner;
  $('shareDescription').textContent=d.is_owner?'Give a teammate access to view and edit this document.':'This document has been shared with you.';
  $('shareUser').innerHTML=Object.values(names).map((name,i)=>({id:i+1,name})).filter(u=>u.id!==d.owner_id&&!d.shared_with.some(s=>s.id===u.id)).map(u=>`<option value="${u.id}">${escapeHTML(u.name)}</option>`).join('');
  $('grantShare').disabled=!$('shareUser').options.length;
  let members=[{id:d.owner_id,name:d.owner_name,role:'Owner'},...d.shared_with.map(u=>({...u,role:'Editor'}))];
  $('shareList').innerHTML=members.map(u=>`<div class="share-member"><div class="avatar">${escapeHTML(u.name.split(' ').map(p=>p[0]).join(''))}</div><div><strong>${escapeHTML(u.name)}</strong><small>${escapeHTML(u.role)}</small></div>${d.is_owner&&u.id!==d.owner_id?`<button data-unshare="${u.id}" aria-label="Remove ${escapeHTML(u.name)} access">Remove</button>`:`<span class="role">${escapeHTML(u.role)}</span>`}</div>`).join('');
  document.querySelectorAll('[data-unshare]').forEach(el=>el.onclick=()=>updateShare('DELETE',Number(el.dataset.unshare)));
}
async function updateShare(method,id){
  try {await flush();const d=state.current;const {document:updated}=await api('/documents/'+d.id+'/share'+(method==='DELETE'?'/'+id:''),{method, ...(method==='POST'?{body:JSON.stringify({user_id:id})}:{})});state.current=updated;state.docs=state.docs.map(x=>x.id===updated.id?updated:x);renderShare();notify(method==='POST'?'Access granted.':'Access removed.');}
  catch(err){notify(err.message);}
}
$('newDoc').onclick=()=>createDoc();$('heroNew').onclick=()=>createDoc();$('emptyNew').onclick=()=>createDoc();
$('fileUpload').onchange=e=>doImport(e.target.files[0]);
document.querySelectorAll('.nav').forEach(el=>el.onclick=async()=>{try{await flush();state.view=el.dataset.view;showHome();renderHome();}catch(err){notify(err.message);}});
$('backHome').onclick=async()=>{try{await flush();showHome();await loadDocs();}catch(err){notify(err.message);}};
$('userSwitch').onchange=async e=>{const previous=state.user;try{await flush();state.user=Number(e.target.value);$('profileName').textContent=names[state.user];$('avatar').textContent=names[state.user].split(' ').map(p=>p[0]).join('');showHome();await loadDocs();}catch(err){state.user=previous;e.target.value=String(previous);notify(err.message);}};
$('docTitle').addEventListener('input',edit);$('editor').addEventListener('input',edit);
$('editor').addEventListener('paste',e=>{e.preventDefault();let text=e.clipboardData.getData('text/plain');document.execCommand('insertText',false,text);});
document.querySelectorAll('[data-command]').forEach(el=>el.addEventListener('mousedown',e=>e.preventDefault()));
document.querySelectorAll('[data-command]').forEach(el=>el.onclick=()=>{$('editor').focus();document.execCommand(el.dataset.command,false,null);edit();});
$('formatBlock').onchange=e=>{$('editor').focus();document.execCommand('formatBlock',false,e.target.value);edit();};
$('shareBtn').onclick=async()=>{try{await flush();renderShare();}catch(err){notify(err.message);}};
$('closeModal').onclick=()=>{$('modalOverlay').hidden=true;};
$('modalOverlay').onclick=e=>{if(e.target===$('modalOverlay'))$('modalOverlay').hidden=true;};
$('grantShare').onclick=()=>updateShare('POST',Number($('shareUser').value));
$('deleteBtn').onclick=async()=>{if(!state.current||!state.current.is_owner)return;if(!confirm(`Delete “${state.current.title}”? This cannot be undone.`))return;try{await api('/documents/'+state.current.id,{method:'DELETE'});state.dirty=false;showHome();await loadDocs();notify('Document deleted.');}catch(err){notify(err.message);}};
document.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key==='s'){e.preventDefault();saveDoc();} if(e.key==='Escape')$('modalOverlay').hidden=true;if(e.key.toLowerCase()==='n'&&!e.ctrlKey&&!e.metaKey&&!['INPUT','TEXTAREA'].includes(document.activeElement.tagName)&&document.activeElement.id!=='editor')createDoc();});
window.addEventListener('beforeunload',e=>{if(state.dirty){e.preventDefault();e.returnValue='';}});
loadDocs().catch(err=>notify(err.message));
