"""Local PPTX export using an editable template and Python's standard library."""
from copy import deepcopy
from io import BytesIO
from pathlib import Path
import re
import textwrap
import xml.etree.ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED

P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
REL = 'http://schemas.openxmlformats.org/package/2006/relationships'
CT = 'http://schemas.openxmlformats.org/package/2006/content-types'
for prefix, uri in [('p', P), ('a', A), ('r', R)]:
    ET.register_namespace(prefix, uri)


def parse_slides(text):
    slides = []
    current = None
    notes = False
    for raw in text.splitlines():
        line = raw.strip()
        if not line or re.fullmatch(r'[-*_]{3,}', line):
            continue
        clean = re.sub(r'[*`]', '', line).strip()
        note_ref = re.match(r'^[-•]?\s*Slide\s+(\d+):\s*(.*)$', clean, re.I) if notes else None
        if note_ref and 0 < int(note_ref[1]) <= len(slides):
            slides[int(note_ref[1])-1]['notes'].append(note_ref[2])
            continue
        match = re.match(r'^(?:#{1,6}\s*)?slide\s+\d+\s*(?:[:.·|—–-]\s*)?(.*)$', clean, re.I)
        heading = re.match(r'^#{1,6}\s+(.+)$', clean)
        if match or (heading and not re.match(r'(speaker\s+)?notes\b', heading[1], re.I)):
            title = (match[1] if match else heading[1]).strip() or f'Slide {len(slides)+1}'
            if len(title) > 120:
                raise ValueError('Shorten slide titles to at most 120 characters before making PowerPoint.')
            current = {'title': title, 'body': [], 'notes': []}
            slides.append(current)
            notes = False
            continue
        if current is None:
            # Introductory text is retained rather than silently discarded.
            current = {'title': 'Introduction', 'body': [], 'notes': []}
            slides.append(current)
        note = re.match(r'^(?:#{1,6}\s*)?(?:speaker\s+notes|notes)\b\s*:?\s*(.*)$', clean, re.I)
        if note:
            notes = True
            if note[1]:
                current['notes'].append(note[1])
        elif clean.lower().rstrip(':') not in ('content', 'slide content', 'bullets', 'bullet points'):
            current['notes' if notes else 'body'].append(re.sub(r'^[-*+]\s+', '• ', clean))
    return slides


def plan_slides(slides, source):
    """Choose layouts from explicit structure; never infer facts or chronology."""
    planned = []
    for slide in slides:
        groups = []
        group = {**slide, 'body': [], 'sequence': False}
        pending_label = ''
        for line in slide['body']:
            line = line.lstrip('• ').strip()
            if line.endswith(':') and not re.search(r'sequence|timeline|steps|process', line, re.I):
                pending_label = line+' '
                continue
            if line.endswith(':'):
                if group['body']:
                    groups.append(group)
                label = line[:-1]
                group = {**slide, 'title': label, 'body': [], 'sequence': bool(re.search(r'sequence|timeline|steps|process', label, re.I))}
            else:
                group['body'].append(pending_label+line)
                pending_label = ''
        if group['body'] or not groups:
            groups.append(group)
        for group in groups:
            items = []
            for line in group['body']:
                label, sep, body = line.partition(':')
                if not sep or len(label) > 45:
                    label, body = '', line
                # ponytail: length budgets keep native text readable; no AI rewrite during export.
                chunks = textwrap.wrap(body.strip(), width=180, break_long_words=True, break_on_hyphens=False) or ['']
                items.extend((label + (' (continued)' if i and label else ''), chunk) for i, chunk in enumerate(chunks))
            if not items:
                items = [('', '')]
            # The cover has a lead and three short supporting facts. Dense openings use a focus layout.
            cover = not planned and len(items) <= 4 and all(len(t) <= 100 for _, t in items[1:])
            size = 4 if cover or group['sequence'] else 3
            for offset in range(0, len(items), size):
                batch = items[offset:offset+size]
                kind = 1 if cover and offset == 0 else 3 if group['sequence'] else 4 if len(batch) <= 2 else 2
                values = {f'{{{{{field}{i}}}}}': '' for field in ('TEXT', 'LABEL') for i in range(1,5)}
                for i, (label, body) in enumerate(batch, 1):
                    if kind == 3:
                        values[f'{{{{LABEL{i}}}}}'] = str(offset+i).zfill(2)
                        values[f'{{{{TEXT{i}}}}}'] = (label+': ' if label else '')+body
                    else:
                        values[f'{{{{LABEL{i}}}}}'] = label
                        values[f'{{{{TEXT{i}}}}}'] = body
                # The lead label has no separate cover field; retain it with its text.
                if kind == 1 and batch[0][0]:
                    values['{{TEXT1}}'] = batch[0][0]+': '+batch[0][1]
                planned.append({'kind': kind, 'title': group['title']+(' (continued)' if offset else ''), 'notes': '\n'.join(group['notes']), 'values': values})
    planned.append({'kind':5, 'title':'Source & review', 'notes':'Full source supplied with this draft:\n\n'+source,
                    'values':{'{{TEXT1}}':'This deck was prepared from user-supplied material. The full source is preserved in this slide’s speaker notes.', '{{TEXT2}}':'Review names, dates, attribution and claims before sharing.'}})
    return planned


def xml(root):
    content = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    if root.tag in (f'{{{CT}}}Types', f'{{{REL}}}Relationships'):
        content = content.replace(b'ns0:', b'').replace(b'xmlns:ns0=', b'xmlns=')
    return content


def fill(template, values):
    root = ET.fromstring(template)
    for parent in root.iter():
        for paragraph in list(parent):
            if paragraph.tag != f'{{{A}}}p':
                continue
            texts = paragraph.findall(f'.//{{{A}}}t')
            token = ''.join(t.text or '' for t in texts)
            if token not in values:
                continue
            index = list(parent).index(paragraph)
            parent.remove(paragraph)
            for offset, line in enumerate(values[token].split('\n') or ['']):
                clone = deepcopy(paragraph)
                runs = clone.findall(f'.//{{{A}}}t')
                runs[0].text = line
                if token == '{{TITLE}}' and len(line) > 65:
                    for props in clone.findall(f'.//{{{A}}}rPr'):
                        props.set('sz', '2100')
                for run in runs[1:]:
                    run.text = ''
                parent.insert(index+offset, clone)
    return xml(root)


def make_powerpoint(data):
    if not isinstance(data, dict):
        raise ValueError('Expected presentation data.')
    for key, limit in [('draft', 30000), ('source', 50000), ('title', 100)]:
        value = data.get(key)
        if not isinstance(value, str) or not value.strip() or len(value) > limit:
            raise ValueError(f'Provide nonempty {key} text (maximum {limit} characters).')
        if any(ord(c) < 32 and c not in '\n\r\t' for c in value):
            raise ValueError('Remove unsupported control characters from the presentation.')
    slides = plan_slides(parse_slides(data['draft']), data['source'])
    if len(slides) > 100:
        raise ValueError('This export exceeds 100 slides. Shorten the draft or source.')
    with ZipFile(Path(__file__).with_name('slide-template.pptx')) as template:
        files = {name: template.read(name) for name in template.namelist()}
    templates = dict(files)
    files = {name: content for name, content in files.items() if not name.startswith(('ppt/slides/', 'ppt/notesSlides/'))}
    presentation = ET.fromstring(files['ppt/presentation.xml'])
    ids = presentation.find(f'{{{P}}}sldIdLst')
    ids.clear()
    rels = ET.fromstring(files['ppt/_rels/presentation.xml.rels'])
    for rel in list(rels):
        if rel.get('Type') == R+'/slide':
            rels.remove(rel)
    types = ET.fromstring(files['[Content_Types].xml'])
    for part in list(types):
        if part.get('PartName','').startswith(('/ppt/slides/','/ppt/notesSlides/')):
            types.remove(part)
    for i, slide in enumerate(slides, 1):
        ET.SubElement(ids, f'{{{P}}}sldId', {'id': str(255+i), f'{{{R}}}id': f'relaySlide{i}'})
        ET.SubElement(rels, f'{{{REL}}}Relationship', {'Id': f'relaySlide{i}', 'Type': R+'/slide', 'Target': f'/ppt/slides/slide{i}.xml'})
        kind = slide['kind']
        values = {**slide['values'], '{{TITLE}}':slide['title'], '{{SECTION}}':data['title'], '{{FOOTER}}':f'Relay  /  {i:02d}     ·     Draft — review before sharing', '{{NOTES}}':slide['notes']}
        files[f'ppt/slides/slide{i}.xml'] = fill(templates[f'ppt/slides/slide{kind}.xml'], values)
        files[f'ppt/notesSlides/notesSlide{i}.xml'] = fill(templates[f'ppt/notesSlides/notesSlide{kind}.xml'], values)
        files[f'ppt/slides/_rels/slide{i}.xml.rels'] = templates[f'ppt/slides/_rels/slide{kind}.xml.rels'].replace(f'notesSlide{kind}.xml'.encode(), f'notesSlide{i}.xml'.encode())
        files[f'ppt/notesSlides/_rels/notesSlide{i}.xml.rels'] = templates[f'ppt/notesSlides/_rels/notesSlide{kind}.xml.rels'].replace(f'/slide{kind}.xml'.encode(), f'/slide{i}.xml'.encode())
        for part, content_kind in [(f'/ppt/slides/slide{i}.xml', 'slide'), (f'/ppt/notesSlides/notesSlide{i}.xml', 'notesSlide')]:
            ET.SubElement(types, f'{{{CT}}}Override', {'PartName': part, 'ContentType': f'application/vnd.openxmlformats-officedocument.presentationml.{content_kind}+xml'})
    files['ppt/presentation.xml'] = xml(presentation)
    files['ppt/_rels/presentation.xml.rels'] = xml(rels)
    files['[Content_Types].xml'] = xml(types)
    output = BytesIO()
    with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return output.getvalue()
