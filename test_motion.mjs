import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';

const source=readFileSync(new URL('./motion.js',import.meta.url),'utf8');
function setup(saved,reducedMotion=false,blockedStorage=false){
  const stored=new Map(saved?[['relay-motion',saved]]:[]);
  const button={setAttribute(key,value){this[key]=value;}};
  const reduced={matches:reducedMotion,addEventListener(_,callback){this.change=callback;}};
  const document={documentElement:{dataset:{}},querySelectorAll:selector=>selector==='.motion-toggle'?[button]:[]};
  runInNewContext(source,{document,matchMedia:query=>query.includes('reduced-motion')?reduced:{matches:true},localStorage:{
    getItem(key){if(blockedStorage)throw Error('Blocked');return stored.get(key);},
    setItem(key,value){if(blockedStorage)throw Error('Blocked');stored.set(key,value);}
  }});
  return {stored,button,reduced,state:()=>document.documentElement.dataset.motion};
}

let page=setup();
assert.equal(page.state(),'on');
page.button.onclick();
assert.equal(page.state(),'off');
assert.equal(page.button['aria-pressed'],'false');
assert.equal(setup(page.stored.get('relay-motion')).state(),'off');
page.button.onclick();
assert.equal(page.stored.get('relay-motion'),'on');
page.reduced.matches=true;page.reduced.change();
assert.equal(page.state(),'off');
assert.equal(page.button.disabled,true);
page.reduced.matches=false;page.reduced.change();
assert.equal(page.state(),'on');
assert.equal(page.button.disabled,false);
assert.equal(setup('on',true).state(),'off');
page=setup(undefined,false,true);page.button.onclick();
assert.equal(page.state(),'off');
console.log('PASS: motion toggles, persists, respects reduced motion, and tolerates blocked storage.');
