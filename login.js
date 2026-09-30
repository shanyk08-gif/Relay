(async()=>{
 const status=document.getElementById('login-status');
 try{
  const sessionResponse=await fetch('/api/session');
  if(!sessionResponse.ok)throw Error('Relay login status is unavailable. Reload to retry.');
  const session=await sessionResponse.json();
  if(session.hosted){document.querySelector('.login-reassurance p').textContent='Your workspace, wherever you sign in. Campaigns are saved securely to your Relay account.';document.querySelector('.login-privacy').textContent='Relay uses your Google profile for sign-in. Campaigns are stored with Supabase. Generating AI drafts sends your source to Google. No Gmail, Drive or contacts access is requested.';}
  if(session.authenticated){location.replace('/');return;}
  const response=await fetch('/api/login/config');const config=await response.json();
  if(!response.ok)throw Error(config.error||'Login is unavailable.');
  if(!config.enabled){location.replace('/');return;}
  const script=document.createElement('script');script.src='https://accounts.google.com/gsi/client';
  script.onload=()=>{
   google.accounts.id.initialize({client_id:config.client_id,nonce:config.nonce,auto_select:false,callback:async({credential})=>{
    status.textContent='Signing in…';
    try{const response=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({credential})});const result=await response.json();if(!response.ok)throw Error(result.error||'Sign-in failed.');
     const check=await fetch('/api/session');const session=await check.json();
     if(!check.ok||!session.authenticated)throw Error('Relay could not confirm the login session. Restart Relay and reload this page; if it persists, check that cookies are allowed.');
     location.replace('/');}
    catch(error){status.textContent=error.message+' Reload this page to retry.';}
   }});
   google.accounts.id.renderButton(document.getElementById('google-button'),{theme:'outline',size:'large'});status.textContent='';
  };
  script.onerror=()=>status.textContent='Google sign-in could not load. Check your internet connection and reload.';
  document.head.append(script);
 }catch(error){status.textContent=error.message;}
})();
