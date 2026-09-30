import assert from 'node:assert/strict';
import {sections,campaignGroups,importCopies} from './preview.mjs';
for(const [format,text] of [['slides','Preface\n\n### Slide 1: Facts\n- <script>alert(1)</script>\n\n**Slide 2: Detail**\nSpeaker notes: Keep attribution.'],['video','Scene 1: Open\nWords\nScene 2: Close\nMore words'],['summary','A\n\nB']])assert.equal(sections(text,format).join('\n'),text);
const root={id:'a',title:'Same name'},version={id:'b',familyId:'a'},unrelated={id:'c',title:'Same name'};
assert.deepEqual(campaignGroups([version,unrelated,root]),[[version,root],[unrelated]]);
console.log('PASS: previews preserve all text and version grouping uses identity, not titles.');

const imported=importCopies([version,unrelated,root]);
assert.equal(campaignGroups(imported).length,2);
assert.equal(imported[0].familyId,imported[2].id);
assert.notEqual(imported[0].familyId,importCopies([version])[0].familyId);
assert.notEqual(imported[2].id,root.id);
assert.equal(root.id,'a');
