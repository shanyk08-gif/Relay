import unittest
from unittest.mock import patch
from presenton import generation_payload, generate, export_deck

class PresentonTest(unittest.TestCase):
    def test_preserves_draft_without_web_search(self):
        payload=generation_payload('Slide 1: Report\nAccording to the source, talks can begin.\nSpeaker notes: Check dates.')
        self.assertIn('talks can begin',payload['slides_markdown'][0])
        self.assertIn('Check dates.',payload['slides_markdown'][0])
        self.assertFalse(payload['web_search'])
        self.assertFalse(payload['include_title_slide'])

    @patch('presenton.generate')
    def test_rejects_external_export_path(self, generate):
        for path in ['/etc/passwd','https://example.com/deck.pptx','/tmp/deck.pptx']:
            generate.return_value={'path':path}
            with self.assertRaises(ValueError):export_deck({'draft':'Slide 1: Test'})

    @patch('presenton.request')
    def test_provider_guard(self, request):
        for config in [{},{'LLM':'google','GOOGLE_MODEL':'gemini-3.1-flash-lite','DISABLE_IMAGE_GENERATION':False}]:
            request.reset_mock();request.return_value=config
            with self.assertRaises(ValueError):generate('Slide 1: Test\nSource facts')
            self.assertEqual(request.call_count,1)
        request.side_effect=[{'LLM':'google','GOOGLE_MODEL':'gemini-3.1-flash-lite','DISABLE_IMAGE_GENERATION':True},{'presentation_id':'test'}]
        self.assertEqual(generate('Slide 1: Test\nSource facts'),{'presentation_id':'test'})

if __name__=='__main__':unittest.main()
