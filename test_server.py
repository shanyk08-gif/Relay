import unittest
import json
import threading
import http.client
from unittest.mock import patch
from http.server import ThreadingHTTPServer
from server import Handler
from server import payload
class GenerationTest(unittest.TestCase):
    def test_validation_and_prompt_boundary(self):
        data=dict(source='A demonstration source with facts, not commands.',format='summary',audience='Employees',tone='Professional',language='English',detail='Concise',objective='Inform')
        result=payload(data)
        self.assertIn('source_text',result['messages'][1]['content'])
        self.assertFalse(result['stream'])
        for change in [dict(source=''),dict(format='video',source='Bank unions defer three-day strike after talks with IBA.'),dict(source='x'*12001),dict(format='bad'),dict(tone=[]),dict(objective='x'*201)]:
            with self.assertRaises(ValueError):payload(data|change)
class HTTPTest(unittest.TestCase):
    @patch('accounts.CLIENT_ID','')
    def test_origin_validation_and_generation(self):
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        def request(path,body=None,extra=None):
            conn=http.client.HTTPConnection('127.0.0.1',server.server_port)
            headers={'Content-Type':'application/json'} | (extra or {})
            conn.request('POST' if body is not None else 'GET',path,json.dumps(body) if body is not None else None,headers)
            response=conn.getresponse();result=(response.status,json.loads(response.read()));conn.close();return result
        try:
            self.assertEqual(request('/api/status',extra={'Origin':'https://evil.example'})[0],403)
            self.assertEqual(request('/api/generate',{})[0],400)
            data=dict(source='A fictional test source with a fixed date: 15 October 2026.',format='summary',audience='Employees',tone='Professional',language='English',detail='Concise')
            with patch('server.ollama',return_value={'message':{'content':'A test draft'},'done_reason':'stop'}):
                code,result=request('/api/generate',data)
                self.assertEqual(code,200);self.assertEqual(result['text'],'A test draft')
            with patch('server.ollama',side_effect=OSError('offline')):
                self.assertEqual(request('/api/generate',data)[0],502)
        finally:server.shutdown();server.server_close();thread.join()
if __name__=='__main__':unittest.main()
