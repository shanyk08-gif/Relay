import io
import json
import unittest
import urllib.error
from unittest.mock import patch
from server import gemini

class GeminiTest(unittest.TestCase):
    def test_request_and_response(self):
        response={'candidates':[{'finishReason':'STOP','content':{'parts':[{'thought':True,'text':'hidden'},{'text':'Draft'}]}}]}
        with patch.dict('os.environ',{'GEMINI_API_KEY':'test-key'}), patch('server.urllib.request.urlopen',return_value=io.BytesIO(json.dumps(response).encode())) as call:
            result=gemini({'messages':[{'content':'system'},{'content':'source'}]})
            self.assertEqual(result['message']['content'],'Draft')
            request=call.call_args.args[0]
            self.assertNotIn('test-key',request.full_url)
            self.assertEqual(json.loads(request.data)['contents'][0]['parts'][0]['text'],'source')
    def test_quota_and_missing_key(self):
        with patch.dict('os.environ',{'GEMINI_API_KEY':''}):
            with self.assertRaisesRegex(ValueError,'key missing'):gemini({})
        with patch.dict('os.environ',{'GEMINI_API_KEY':'test-key'}), patch('server.urllib.request.urlopen',side_effect=urllib.error.HTTPError('https://example.com',429,'quota',{},None)):
            with self.assertRaisesRegex(ValueError,'no paid fallback'):gemini({'messages':[{'content':'system'},{'content':'source'}]})
if __name__=='__main__':unittest.main()
