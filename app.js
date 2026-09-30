import {FORMATS,campaign,sample,wordCount,excerpts,setSource,setDraft,markdown,validCampaign,stale,stamp,socialDraft} from './model.mjs?v=6';
const $=id=>document.getElementById(id), KEY='relay-studio-v1';
let campaigns=[], current, storageError='', toastTimer, accountMode=false, hostedMode=false, workspaceSession='', accountProfile={}, saving=Promise.resolve(), pendingSaves=0, saveFailed=false;
function tell(message){$('toast').textContent=message;$('toast').hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').hidden=true,4500);}
try{
  const response=await fetch('/api/session');if(!response.ok)throw Error('Login status unavailable.');
  const session=await response.json();accountMode=session.enabled;hostedMode=session.hosted===true;workspaceSession=session.workspace_session;accountProfile=session.profile||{};
  if(accountMode&&!session.authenticated){location.replace('/login');throw Error('Sign in to continue.');}
  let saved;
  if(accountMode){const response=await fetch('/api/workspace');if(!response.ok)throw Error('Account workspace unavailable.');saved=await response.json();}
  else saved=JSON.parse(localStorage.getItem(KEY)||'[]');
  if(!Array.isArray(saved)||!saved.every(validCampaign))throw Error('Invalid saved workspace');campaigns=saved;
}catch{storageError='Saved data could not be loaded. It will not be overwritten. Reload to retry; export any new work before leaving.';}
if(!campaigns.length)campaigns=[campaign()];current=campaigns[0];
function save(){
 current.updated=new Date().toISOString();renderNav();
 if(storageError){$('save-status').textContent='Not saved · export a backup';return;}
 const snapshot=JSON.stringify(campaigns);
 if(!accountMode){try{localStorage.setItem(KEY,snapshot);$('save-status').textContent='Saved in this browser';}catch{$('save-status').textContent='Not saved · export a backup';}return;}
 $('save-status').textContent='Saving…';pendingSaves++;
 saving=saving.then(async()=>{
   try{const response=await fetch('/api/workspace',{method:'POST',headers:{'Content-Type':'application/json','X-Workspace-Session':workspaceSession},body:snapshot});if(!response.ok){const result=await response.json();throw Error(result.error||'Save failed.');}saveFailed=false;}
   catch(error){saveFailed=true;tell(error.message+' Export a backup before leaving.');}
   finally{pendingSaves--;if(!pendingSaves)$('save-status').textContent=saveFailed?'Not saved · export a backup':(hostedMode?'Saved to your account':'Saved to your account on this Mac');}
 });
}
window.addEventListener('beforeunload',event=>{if(accountMode&&(pendingSaves||saveFailed)){event.preventDefault();event.returnValue='';}});
$('account-menu').hidden=!accountMode;
if(hostedMode){document.querySelector('.account-dropdown p').textContent='Workspace saved to your account';document.querySelector('footer').firstChild.textContent='Saved to your account · Export to keep a backup · ';}
$('account-name').textContent=accountProfile.name||'Google account';
$('account-email').textContent=accountProfile.email||'';
$('avatar-initial').textContent=(accountProfile.name||'G').trim().slice(0,1).toUpperCase();
if(accountProfile.picture){const photo=$('avatar-photo');photo.onload=()=>{photo.hidden=false;$('avatar-initial').hidden=true;};photo.onerror=()=>{photo.hidden=true;$('avatar-initial').hidden=false;};photo.src=accountProfile.picture;}
document.addEventListener('click',event=>{if(!$('account-menu').contains(event.target))$('account-menu').open=false;});
$('account-menu').addEventListener('keydown',event=>{if(event.key==='Escape'){$('account-menu').open=false;$('account-menu').querySelector('summary').focus();}});
$('logout').onclick=async()=>{
 await saving;if(saveFailed||storageError)return tell('Export a backup before signing out: your latest changes are not saved.');
 try{const response=await fetch('/api/logout',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});if(!response.ok)throw Error();location.replace('/login');}catch{tell('Could not sign out. Please try again.');}
};
$('import-browser').hidden=!accountMode;
$('import-browser').onclick=()=>ask('Import browser campaigns?','Copy campaigns saved in this browser into this Google account on this Mac? The originals remain in browser storage.',()=>{
 try{const old=JSON.parse(localStorage.getItem(KEY)||'[]');if(!Array.isArray(old)||!old.every(validCampaign))throw Error();if(!old.length)return tell('No campaigns found at this browser address. Your old 127.0.0.1 workspace is separate from localhost.');if(campaigns.length+old.length>200)return tell('Import would exceed 200 campaigns.');campaigns.unshift(...old.map(c=>({...c,id:crypto.randomUUID()})));current=campaigns[0];save();render();tell('Browser campaigns copied to this account.');}catch{tell('Browser campaigns could not be imported. Originals are unchanged.');}
});
function renderNav(){$('campaigns').replaceChildren(...campaigns.map(c=>{const b=document.createElement('button');b.textContent=c.title||'Untitled campaign';b.setAttribute('aria-current',String(c.id===current.id));const small=document.createElement('small');small.textContent=c.sample?'CURATED SAMPLE':'MANUAL WORKSPACE';b.append(small);b.onclick=()=>{current=c;render();};return b;}));}
function renderEvidence(){const chunks=excerpts(current.source);$('excerpts').replaceChildren(...chunks.map((text,i)=>{const q=document.createElement('blockquote'),tag=document.createElement('span');tag.textContent=`S${i+1}`;q.append(tag,document.createTextNode(text));return q;}));if(!chunks.length)$('excerpts').textContent='Add source material to compare it with your drafts.';$('source-count').textContent=`${wordCount(current.source)} words · ${hostedMode?'saved to your account':accountMode?'saved on this Mac':'stays in this browser'}`;}
function renderSocial(){
  const host=$('social-actions');host.replaceChildren();host.hidden=!['linkedin','thread'].includes(current.active);
  if(host.hidden)return;
  const hint=document.createElement('p');hint.className='small muted';hint.textContent='Review and mark your draft first. Each button asks before copying and opening the platform. Paste and publish there yourself.';host.append(hint);
  const d=current.drafts[current.active],posts=current.active==='thread'?excerpts(d.text):[d.text];
  posts.forEach((text,index)=>{const button=document.createElement('button');button.textContent=current.active==='thread'?`Copy post ${index+1} & open X ↗`:'Copy & open LinkedIn ↗';button.disabled=!d.text.trim()||!d.reviewed||stale(current,d);button.onclick=()=>sharePost(index);host.append(button);});
}
function renderStats(){renderSocial();const d=current.drafts[current.active];$('reviewed').checked=d.reviewed&&!stale(current,d);$('reviewed').disabled=!d.text.trim()||!current.source.trim()||stale(current,d);$('draft-status').textContent=(stale(current,d)?'Outdated / source unlinked — regenerate':d.reviewed?'Reviewed by you':d.text.trim()?'Needs review':'Empty draft')+(d.model?' · AI: '+d.model:'');let count=`${wordCount(d.text)} words · ${d.text.length} characters`;if(current.active==='thread'){const posts=excerpts(d.text);count+=` · ${posts.filter(p=>Array.from(p).length>280).length} posts over 280 characters (basic count)`;}$('draft-count').textContent=count;$('progress').textContent=`${Object.values(current.drafts).filter(v=>v.reviewed&&!stale(current,v)).length} / 7 reviewed`;$('copy').disabled=$('export').disabled=!d.text.trim()||stale(current,d);$('presenton').hidden=hostedMode||current.active!=='slides';$('powerpoint').hidden=current.active!=='slides';$('presenton').disabled=!d.text.trim()||stale(current,d);$('powerpoint').disabled=!d.text.trim()||stale(current,d);$('bundle').disabled=!Object.values(current.drafts).some(v=>v.text.trim()&&!stale(current,v));}
function renderEditor(){for(const b of $('formats').children)b.setAttribute('aria-pressed',String(b.dataset.key===current.active));$('format-title').textContent=FORMATS[current.active][0];$('draft-hint').textContent=FORMATS[current.active][1];$('draft').value=current.drafts[current.active].text;$('draft').readOnly=stale(current,current.drafts[current.active]);$('draft').placeholder='Write a draft or select Generate selected format. AI creates a new campaign version to preserve your current work.';renderStats();}
function render(){renderNav();for(const k of ['title','source','audience','tone','language','detail','objective'])$(k).value=current[k];$('source-kind').textContent=current.sample?'Curated sample':'Manual workspace';renderEvidence();renderEditor();}
for(const [key,[name]]of Object.entries(FORMATS)){const b=document.createElement('button');b.textContent=name;b.dataset.key=key;b.onclick=()=>{current.active=key;save();renderEditor();};$('formats').append(b);}
for(const k of ['title','audience','tone','language','detail','objective'])$(k).addEventListener('input',()=>{current[k]=$(k).value;if(k!=='title')Object.values(current.drafts).forEach(d=>d.reviewed=false);save();renderEditor();});
$('source').oninput=()=>{setSource(current,$('source').value);$('objective').value='';save();renderEvidence();renderEditor();$('source-kind').textContent='Manual workspace';};
$('draft').oninput=()=>{setDraft(current,$('draft').value);save();renderStats();};
$('reviewed').onchange=()=>{current.drafts[current.active].reviewed=$('reviewed').checked;save();renderStats();};
function add(c){campaigns.unshift(c);current=c;save();render();$('title').focus();}
$('new').onclick=()=>add(campaign());$('sample').onclick=()=>{const existing=campaigns.find(c=>c.sample);if(existing){current=existing;render();tell('Opened the saved sample. Your edits are preserved.');}else add(sample());};
$('file').onchange=async()=>{const f=$('file').files[0];$('file').value='';if(!f)return;if(!/\.(txt|md)$/i.test(f.name)||f.size>150000)return tell('Choose a .txt or .md file smaller than 150 KB.');const target=current;try{const text=await f.text();if(text.length>50000||text.includes('\0'))return tell('Use a text file with at most 50,000 characters.');const apply=()=>{setSource(target,text);if(current!==target)current=target;save();render();tell('Source imported. Existing drafts need review.');};if(target.source.trim())ask('Replace source material?','Existing drafts stay in the campaign, and all review marks will reset.',apply);else apply();}catch{tell('The file could not be read. Try pasting the text.');}};
function download(text,name){const url=URL.createObjectURL(text instanceof Blob?text:new Blob([text],{type:'text/markdown;charset=utf-8'})),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);tell('Export prepared. Check your downloads.');}
function filename(){return(current.title.replace(/[^a-z0-9]+/gi,'-').replace(/^-|-$/g,'').slice(0,70)||'campaign');}
$('export').onclick=()=>download(markdown(current,current.active),`${filename()}-${current.active}.md`);$('bundle').onclick=()=>download(markdown(current),`${filename()}-campaign.md`);
$('copy').onclick=async()=>{try{await navigator.clipboard.writeText(current.drafts[current.active].text);tell('Draft copied.');}catch{tell('Clipboard unavailable. Select the draft and copy it manually.');}};
let confirmed=()=>{};function ask(title,text,fn,info=false){$('dialog-title').textContent=title;$('dialog-text').textContent=text;$('cancel').hidden=info;$('confirm').textContent=info?'Got it':'Continue';confirmed=fn;$('dialog').showModal();}
$('cancel').onclick=()=>$('dialog').close();$('confirm').onclick=()=>{$('dialog').close();confirmed();};
$('delete').onclick=()=>ask('Delete this campaign?','This removes the campaign from this workspace. Export a backup first if you want to keep it.',()=>{campaigns=campaigns.filter(c=>c.id!==current.id);if(!campaigns.length)campaigns=[campaign()];current=campaigns[0];save();render();});
$('about').onclick=()=>ask('Relay · SIH26154 prototype','This interface supports seven editable formats, plain-text import, local saving, review and Markdown exports. Sample content is fictional and manually prepared. The active provider is shown at the top. Gemini sends source text to Google; Ollama runs locally. Generated drafts are unverified and need human review. Google accounts save campaigns separately on this Mac. Browser-only campaigns can be imported after sign-in. PDF/image/video ingestion and team collaboration are not connected.',()=>{},true);
render();if(storageError){$('save-status').textContent='Storage unavailable';tell(storageError);}else save();

let generating=false, ready=false, provider='ollama';
async function checkAI(){
  $('reconnect').disabled=true;
  try{const response=await fetch('/api/status');if(!response.ok)throw Error();const status=await response.json();ready=status.ready===true;provider=status.provider||'ollama';$('connection').textContent=ready?'● '+(provider==='gemini'?'Gemini configured':'Local AI')+' · '+status.model:'○ AI not connected';$('ai-status').textContent=status.message;}
  catch{ready=false;$('connection').textContent='○ AI server unavailable';$('ai-status').textContent='Run python3 server.py from the Relay folder to enable AI.';}
  finally{$('generate').disabled=!ready||generating;$('reconnect').disabled=false;}
}
$('reconnect').onclick=checkAI;
$('generate').onclick=async()=>{
  if(generating||!ready)return;
  if(current.source.trim().length<20||current.source.length>12000)return tell('Use 20–12,000 source characters for generation.');
  if(['video','slides','advisory'].includes(current.active)&&wordCount(current.source)<40)return tell('Add the full article or at least 40 words of source detail for this format. A headline is not enough.');
  const snapshot=structuredClone(current),key=snapshot.active;
  generating=true;$('generate').disabled=true;$('generate').textContent='Generating…';$('ai-status').textContent='Generating your draft. Existing work is preserved.';
  try{
    const response=await fetch('/api/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...snapshot,format:key})});
    const result=await response.json();if(!response.ok)throw Error(result.error||'Generation failed.');
    if(typeof result.text!=='string'||!result.text.trim())throw Error('The model returned no draft.');
    snapshot.id=crypto.randomUUID();snapshot.title=(snapshot.title.split(' · AI ')[0]+' · AI '+FORMATS[key][0]).slice(0,100);snapshot.sample=false;
    snapshot.drafts[key]=stamp(snapshot,{text:result.text,model:result.model});
    add(snapshot);$('ai-status').textContent=result.truncated?'Draft reached the output limit and may be incomplete. Review it before use.':'Created a new campaign version. Original drafts preserved. Check every fact before sharing.';
    tell('AI draft ready in a new campaign version.');
  }catch(error){$('ai-status').textContent=error.message||'Generation failed. Your draft is unchanged.';}
  finally{generating=false;$('generate').disabled=!ready;$('generate').textContent='Generate selected format';}
};
checkAI();

let exportingPowerpoint=false;
$('powerpoint').onclick=async()=>{
  const draft=current.drafts.slides;
  if(exportingPowerpoint||!draft.text.trim()||stale(current,draft))return;
  const data={title:current.title||'Presentation',draft:draft.text,source:draft.source},name=filename();
  exportingPowerpoint=true;$('powerpoint').disabled=true;$('powerpoint').textContent='Making PowerPoint…';
  try{
    const response=await fetch('/api/powerpoint',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
    if(!response.ok){const error=await response.json();throw Error(error.error||'PowerPoint export failed.');}
    download(await response.blob(),`${name}.pptx`);
  }catch(error){tell(error.message||'PowerPoint export failed. Restart Relay to load the latest exporter.');}
  finally{exportingPowerpoint=false;$('powerpoint').textContent='Make PowerPoint ↓';renderStats();}
};

let designing=false;
$('presenton').onclick=()=>{
  if(designing)return;
  const d=current.drafts.slides;
  if(!d.text.trim()||stale(current,d))return;
  const text=d.text,name=filename();
  ask('Design with Presenton?', 'This sends the presentation draft through your local Presenton app to Gemini. It uses your Gemini quota. Keep Presenton open; generation may take several minutes.',async()=>{
    if(designing)return;
    designing=true;$('presenton').disabled=true;$('presenton').textContent='Designing…';
    $('ai-status').textContent='Presenton is designing your deck. Keep this tab open.';
    try{
      const response=await fetch('/api/presenton',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({draft:text})});
      if(!response.ok){const result=await response.json();throw Error(result.error||'Presenton failed.');}
      download(await response.blob(),`${name}-presenton.pptx`);
      $('ai-status').textContent='Presenton deck downloaded. Review facts and layout before sharing.';
    }catch(error){$('ai-status').textContent=error.message||'Presenton connection failed. Your draft is preserved.';}
    finally{designing=false;$('presenton').textContent='Design with Presenton';renderStats();}
  });
};

function sharePost(index){
  const target=current,active=current.active;
  let post;try{post=socialDraft(target,index);}catch(error){return tell(error.message);}
  ask(`Open ${post.platform}?`, `Copy ${active==='thread'?`post ${index+1} of ${post.count}`:'this reviewed post'} and open ${post.platform} in a new tab? Paste it into the composer and review it there. Relay will not publish it.`,()=>{
    try{if(current!==target||current.active!==active||socialDraft(current,index).text!==post.text)throw Error('The draft changed. Review it again before sharing.');}catch(error){return tell(error.message);}
    // Open during the confirmation click so browser popup rules permit the tab.
    window.open(post.url,'_blank','noopener,noreferrer');
    navigator.clipboard.writeText(post.text).then(()=>tell(`Copied. Paste into ${post.platform}. If no tab opened, allow popups for Relay.`)).catch(()=>tell(`Clipboard unavailable. Use Copy or select the text manually, then paste in ${post.platform}.`));
  });
}
