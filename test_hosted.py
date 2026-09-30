import io
import json
import unittest
from contextlib import ExitStack
from unittest.mock import patch
import accounts
import hosted

class HostedTest(unittest.TestCase):
    def setUp(self):
        self.stack=ExitStack();self.addCleanup(self.stack.close)
        for name,value in [('accounts.HOSTED',True),('accounts.CLIENT_ID','test.apps.googleusercontent.com'),('server.HOSTED',True),('server.PUBLIC_ORIGIN','https://relay.example'),('server.SECURE_COOKIE','; Secure')]:
            self.stack.enter_context(patch(name,value))
        self.records={}
        def get(kind,key):return self.records.get((kind,key))
        def put(kind,key,value,expires=None):self.records[(kind,key)]={'value':value,'expires':expires}
        self.stack.enter_context(patch('cloud.get',side_effect=get))
        self.stack.enter_context(patch('cloud.put',side_effect=put))
        self.stack.enter_context(patch('cloud.remove',side_effect=lambda kind,key:self.records.pop((kind,key),None)))
        self.stack.enter_context(patch('cloud.limit',return_value=True))
    def call(self,path,body=None,cookie='',origin='https://relay.example',host='relay.example'):
        raw=json.dumps(body).encode() if body is not None else b''
        environ={'PATH_INFO':path,'REQUEST_METHOD':'POST' if body is not None else 'GET','wsgi.input':io.BytesIO(raw),'CONTENT_LENGTH':str(len(raw)),'CONTENT_TYPE':'application/json','HTTP_HOST':host,'HTTP_ORIGIN':origin,'HTTP_COOKIE':cookie}
        result={}
        def start(status,headers):result.update(status=int(status.split()[0]),headers=headers)
        result['body']=b''.join(hosted.application(environ,start))
        return result
    def sign_in(self):
        config=self.call('/api/login/config')
        nonce=json.loads(config['body'])['nonce']
        login_cookie=next(v.split(';')[0] for k,v in config['headers'] if k=='Set-Cookie')
        with patch('accounts.verify',return_value={'sub':'alice','nonce':nonce,'name':'Alice'}):
            result=self.call('/api/login',{'credential':'fake-credential'},login_cookie)
        self.assertEqual(result['status'],200)
        cookies=[v for k,v in result['headers'] if k=='Set-Cookie']
        self.assertIn('; Secure',cookies[0]);self.assertIn('HttpOnly',cookies[0])
        return cookies[0].split(';')[0]
    def test_cloud_session_roundtrip_and_logout(self):
        cookie=self.sign_in()
        accounts.SESSIONS.clear() # hosted session survives loss of process memory
        session=json.loads(self.call('/api/session',cookie=cookie)['body'])
        self.assertTrue(session['authenticated']);self.assertEqual(session['profile']['name'],'Alice')
        self.assertEqual(self.call('/api/workspace',cookie=cookie)['status'],200)
        self.assertEqual(self.call('/api/logout',{},cookie)['status'],200)
        self.assertFalse(json.loads(self.call('/api/session',cookie=cookie)['body'])['authenticated'])
    def test_public_boundaries_and_database_failure(self):
        self.assertEqual(self.call('/api/session',host='evil.example')['status'],403)
        self.assertEqual(self.call('/api/login',{},origin='https://evil.example')['status'],403)
        self.assertEqual(self.call('/api/workspace')['status'],401)
        with patch('cloud.get',side_effect=OSError('private database error')):
            result=self.call('/api/session',cookie='relay_session=test')
        self.assertEqual(result['status'],503);self.assertNotIn(b'private database',result['body'])
    def test_quota_denies_generation_without_calling_google(self):
        cookie=self.sign_in()
        data=dict(source='This source is sufficiently long for a summary.',format='summary',audience='Employees',tone='Professional',language='English',detail='Concise')
        with patch('cloud.limit',return_value=False),patch('server.gemini') as generate:
            self.assertEqual(self.call('/api/generate',data,cookie)['status'],429)
            generate.assert_not_called()

if __name__=='__main__':unittest.main()
