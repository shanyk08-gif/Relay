import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from http.server import ThreadingHTTPServer
import accounts
from server import Handler

class AccountTest(unittest.TestCase):
    def test_profile_image_host_restricted(self):
        good=accounts.profile_claims({'name':'Example','email':'test@example.com','email_verified':True,'picture':'https://lh3.googleusercontent.com/a/photo'})
        self.assertEqual(good['email'],'test@example.com')
        self.assertTrue(good['picture'])
        for picture in ['javascript:alert(1)','https://evil.example/photo','https://googleusercontent.com.evil.example/photo']:
            self.assertEqual(accounts.profile_claims({'picture':picture})['picture'],'')
        self.assertEqual(accounts.profile_claims({'email':'unverified@example.com'})['email'],'')

    def test_google_cookie_does_not_hide_relay_session(self):
        accounts.ATTEMPTS.clear()
        token,nonce=accounts.challenge()
        google='g_state={"i_l":0,"i_ll":1727670000000,"i_b":"example"}; '
        with patch('accounts.verify',return_value={'sub':'cookie-test','nonce':nonce}):
            session=accounts.login({'Cookie':google+'relay_login='+token},{'credential':'fake-test-token'})
        headers={'Cookie':google+'relay_session='+session}
        self.assertEqual(accounts.user(headers),'cookie-test')
        self.assertEqual(accounts.user({'Cookie':'relay_session='+session+'; '+google}),'cookie-test')
        self.assertIsNone(accounts.user({'Cookie':'relay_session=wrong; relay_session='+session}))
        accounts.logout(headers)
        self.assertIsNone(accounts.user(headers))


    def test_sessions_replay_and_workspace_isolation(self):
        accounts.ATTEMPTS.clear()
        token,nonce=accounts.challenge()
        with patch('accounts.verify',return_value={'sub':'alice','nonce':nonce}):
            session=accounts.login({'Cookie':'relay_login='+token},{'credential':'fake-test-token'})
            with self.assertRaises(ValueError):accounts.login({'Cookie':'relay_login='+token},{'credential':'fake-test-token'})
        headers={'Cookie':'relay_session='+session}
        self.assertEqual(accounts.user(headers),'alice')
        token,nonce=accounts.challenge()
        with patch('accounts.verify',return_value={'sub':'alice','nonce':'wrong'}):
            with self.assertRaises(ValueError):accounts.login({'Cookie':'relay_login='+token},{'credential':'fake-test-token'})
        with tempfile.TemporaryDirectory() as d,patch('accounts.DB',Path(d)/'accounts.sqlite3'):
            c={k:'' for k in ('id','title','source','updated','audience','tone','language','detail','objective')}
            c.update(active='summary',drafts={k:{'text':'private','reviewed':False} for k in ('summary','advisory','linkedin','thread','slides','infographic','video')})
            accounts.workspace('alice',[c]);self.assertEqual(accounts.workspace('alice'),[c]);self.assertEqual(accounts.workspace('bob'),[])
            with self.assertRaises(ValueError):accounts.workspace('alice',[{}])
            self.assertEqual(accounts.workspace('alice'),[c])
        accounts.logout(headers);self.assertIsNone(accounts.user(headers))

    def test_http_requires_login_and_origin(self):
        with patch('accounts.CLIENT_ID','test.apps.googleusercontent.com'):
            server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            def request(method,path,body=None,headers=None):
                conn=http.client.HTTPConnection('127.0.0.1',server.server_port)
                conn.request(method,path,body,headers or {});response=conn.getresponse();status=response.status
                if path=='/login':
                    policy=response.getheader('Content-Security-Policy')
                    self.assertIn("style-src 'self' 'unsafe-inline' https://accounts.google.com/gsi/style",policy)
                    self.assertIn("script-src 'self' https://accounts.google.com/gsi/client;",policy)
                response.read();conn.close();return status
            try:
                self.assertEqual(request('GET','/'),302)
                self.assertEqual(request('GET','/login'),200)
                self.assertEqual(request('GET','/api/workspace'),401)
                self.assertEqual(request('POST','/api/generate','{}',{'Content-Type':'application/json'}),401)
                self.assertEqual(request('POST','/api/login','{}',{'Content-Type':'application/json'}),403)
                origin='http://127.0.0.1:'+str(server.server_port)
                self.assertEqual(request('POST','/api/login','{}',{'Content-Type':'application/json','Origin':origin}),400)
            finally:server.shutdown();server.server_close();thread.join()

if __name__=='__main__':unittest.main()
