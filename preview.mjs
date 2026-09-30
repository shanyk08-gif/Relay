// Presentation-only helpers: never rewrite or persist generated content.
export function sections(text,format){
  const lines=text.split('\n'),parts=[];let block=[];
  for(const line of lines){
    const start=format==='slides'?/^\s*(?:#{1,6}\s*)?(?:\*\*)?Slide\s+\d+\b/i.test(line):format==='video'?/^\s*(?:#{1,6}\s*)?(?:\*\*)?Scene\s+\d+\b/i.test(line):false;
    if(start&&block.length){parts.push(block.join('\n'));block=[];}
    block.push(line);
  }
  if(block.length)parts.push(block.join('\n'));
  return parts;
}
export function campaignGroups(campaigns){
  const groups=new Map();
  for(const c of campaigns){const key=c.familyId||c.id;if(!groups.has(key))groups.set(key,[]);groups.get(key).push(c);}
  return [...groups.values()];
}
export function importCopies(campaigns){
  const ids=new Map();
  const remap=id=>{if(!ids.has(id))ids.set(id,crypto.randomUUID());return ids.get(id);};
  return campaigns.map(c=>({...c,id:remap(c.id),...(c.familyId?{familyId:remap(c.familyId)}:{})}));
}
export function drawPreview(host,text,format){
  host.replaceChildren();host.className='output-preview preview-'+format;
  const make=(tag,cls,value)=>{const e=document.createElement(tag);e.className=cls;e.textContent=value;return e;};
  if(!text.trim()){
    const box=make('div','preview-empty','');box.append(make('span','empty-symbol','✳'),make('h4','','Your next draft starts here'),make('p','','Add your source, choose a format, and generate a draft. Or switch to Edit and write your own.'));host.append(box);return;
  }
  const blocks=format==='thread'?text.split(/\n\s*\n/).filter(x=>x.trim()):sections(text,format);
  blocks.forEach((part,i)=>{
    const card=make('article','preview-card','');
    if(format==='linkedin'||format==='thread'){
      const header=make('div','post-identity','');header.append(make('span','post-avatar','r.'),make('span','','Your publisher · Draft preview'),make('span','platform-label',format==='linkedin'?'in':'𝕏'));card.append(header);
    }else if(format==='slides'||format==='video')card.append(make('div','preview-kicker',`${format==='slides'?'SLIDE CONTENT':'SCRIPT SECTION'} / ${String(i+1).padStart(2,'0')}`));
    card.append(make('div','preview-text',part));
    if(format==='thread')card.append(make('span','post-counter',`${Array.from(part).length} characters · Post ${i+1}`));
    host.append(card);
  });
}
