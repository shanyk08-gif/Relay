import unittest
import json
from unittest.mock import Mock, patch
from server import Handler
from io import BytesIO
from zipfile import ZipFile
import xml.etree.ElementTree as ET
from powerpoint import make_powerpoint, parse_slides, plan_slides, A

class PowerPointTest(unittest.TestCase):
    def test_editable_slides_notes_source_and_pagination(self):
        draft='**Slide 1: Facts & dates**\n- One < two\n**Speaker notes:** Keep attribution.\n\n## Slide 2: Details\n'+'\n'.join('Item '+str(i) for i in range(23))
        parsed=parse_slides(draft)
        self.assertEqual(len(parsed),2)
        self.assertEqual(parsed[0]['notes'],['Keep attribution.'])
        with ZipFile(BytesIO(make_powerpoint(dict(title='Test',draft=draft,source='Original source & evidence')))) as z:
            for name in z.namelist():
                if name.endswith(('.xml','.rels')): ET.fromstring(z.read(name))
            slides=[n for n in z.namelist() if n.startswith('ppt/slides/slide') and n.endswith('.xml')]
            self.assertEqual(len(slides),10)
            text=' '.join(' '.join(ET.fromstring(z.read(n)).itertext()) for n in slides)
            self.assertIn('One < two',text)
            self.assertIn('Item 22',text)
            self.assertIn('Original source &amp; evidence',z.read('ppt/notesSlides/notesSlide10.xml').decode())
            self.assertNotIn('Keep attribution.',text)
            self.assertIn('Keep attribution.',z.read('ppt/notesSlides/notesSlide1.xml').decode())
            self.assertNotIn('{{',text)
            self.assertIn('/slide4.xml',z.read('ppt/notesSlides/_rels/notesSlide4.xml.rels').decode())
    @patch('accounts.CLIENT_ID','')
    def test_endpoint_returns_pptx_and_rejects_invalid_input(self):
        for body, expected in [({'title':'T','draft':'Slide 1: Test\nFacts','source':'Source facts'},200), ({},400)]:
            raw=json.dumps(body).encode()
            handler=object.__new__(Handler)
            handler.path='/api/powerpoint'
            handler.headers={'Content-Type':'application/json','Content-Length':str(len(raw))}
            handler.rfile=BytesIO(raw)
            handler.connection=Mock()
            handler.allowed=lambda:True
            handler.reply=Mock()
            handler.do_POST()
            args=handler.reply.call_args.args
            self.assertEqual(args[0],expected)
            if expected==200:
                self.assertTrue(args[1].startswith(b'PK'))
                self.assertIn('presentation',args[2])

    def test_layouts_and_global_notes(self):
        draft='Slide 1: Overview\nEvent: A reported event\nPlace: Example\nDate: Tuesday\nSlide 2: Details\nSequence of events:\nFirst action\nSecond action\nSlide 3: Profile\nName: Example\nRole: Example\nContext: Reported\nSpeaker notes:\n- Slide 1: Attribute the event.\n- Slide 2: Keep the order.'
        parsed=parse_slides(draft)
        self.assertIn('Attribute the event.',parsed[0]['notes'])
        plan=plan_slides(parsed,'Original source')
        self.assertEqual([s['kind'] for s in plan],[1,3,2,5])
        self.assertEqual(plan[1]['values']['{{TEXT2}}'],'Second action')
        self.assertIn('Original source',plan[-1]['notes'])

    def test_bad_input(self):
        for data in [None,{},dict(title='T',draft='',source='S'),dict(title='T',draft='bad\x00',source='S')]:
            with self.assertRaises(ValueError):make_powerpoint(data)

if __name__=='__main__':unittest.main()
