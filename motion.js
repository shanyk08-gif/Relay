// Decorative motion only; respect the system preference and the reader's choice.
(()=>{
 const reduced=matchMedia('(prefers-reduced-motion: reduce)'),fine=matchMedia('(hover: hover) and (pointer: fine)');
 const buttons=document.querySelectorAll('.motion-toggle'),art=document.querySelectorAll('.motion-art');
 let wanted=true,enabled=false;
 try{wanted=localStorage.getItem('relay-motion')!=='off';}catch{}
 const reset=()=>art.forEach(el=>{el.style.removeProperty('--tilt-x');el.style.removeProperty('--tilt-y');});
 function sync(){
  enabled=wanted&&!reduced.matches;document.documentElement.dataset.motion=enabled?'on':'off';reset();
  buttons.forEach(b=>{b.textContent=reduced.matches?'Reduced motion':enabled?'Ⅱ Motion on':'▷ Motion off';b.setAttribute('aria-pressed',String(enabled));b.disabled=reduced.matches;b.title=reduced.matches?'Following your device’s reduced-motion setting':'Turn decorative motion on or off';});
 }
 buttons.forEach(b=>b.onclick=()=>{wanted=!wanted;try{localStorage.setItem('relay-motion',wanted?'on':'off');}catch{}sync();});
 reduced.addEventListener('change',sync);
 art.forEach(el=>{
  el.addEventListener('pointermove',e=>{if(!enabled||!fine.matches)return;const r=el.getBoundingClientRect();el.style.setProperty('--tilt-x',`${(e.clientY-r.top-r.height/2)/r.height*-7}deg`);el.style.setProperty('--tilt-y',`${(e.clientX-r.left-r.width/2)/r.width*9}deg`);});
  el.addEventListener('pointerleave',reset);
 });
 sync();
})();
