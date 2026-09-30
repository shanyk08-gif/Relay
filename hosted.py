"""Serve the existing Relay routes through Waitress behind Render's HTTPS proxy."""
import io
import json
import os
from email.message import Message
from types import SimpleNamespace
from urllib.parse import urlsplit
import accounts
import cloud
from server import Handler, PUBLIC_ORIGIN, PROVIDER

class Response(Handler):
    # The WSGI server owns socket parsing, limits and concurrency.
    def __init__(self,environ):
        self.path=environ['PATH_INFO']
        self.headers=Message()
        for key,value in environ.items():
            if key.startswith('HTTP_'):self.headers[key[5:].replace('_','-')]=value
        self.headers['Content-Type']=environ.get('CONTENT_TYPE','')
        self.headers['Content-Length']=environ.get('CONTENT_LENGTH','0') or '0'
        self.rfile=environ['wsgi.input']
        self.wfile=io.BytesIO()
        self.connection=SimpleNamespace(settimeout=lambda _:None)
        self.server=SimpleNamespace(server_port=int(environ.get('SERVER_PORT',10000)))
        self.status=500
        self.response_headers=[]
    def send_response(self,status,message=None):self.status=status
    def send_header(self,key,value):self.response_headers.append((key,value))
    def end_headers(self):pass


def application(environ,start_response):
    response=Response(environ)
    try:
        if environ['REQUEST_METHOD']=='GET':response.do_GET()
        elif environ['REQUEST_METHOD']=='POST':response.do_POST()
        else:response.reply(405,{'error':'Method not allowed.'})
    except (OSError,ValueError):
        response.response_headers=[];response.wfile=io.BytesIO()
        response.reply(503,{'error':'Account storage unavailable. Please retry.'})
    start_response(str(response.status)+' '+Handler.responses[response.status][0],response.response_headers)
    return [response.wfile.getvalue()]


def validate():
    origin=urlsplit(PUBLIC_ORIGIN)
    if not accounts.HOSTED or origin.scheme!='https' or not origin.hostname or origin.path or origin.query or origin.fragment or origin.username:
        raise SystemExit('Hosted mode requires RELAY_HOSTED=1 and a valid HTTPS PUBLIC_ORIGIN.')
    if not accounts.CLIENT_ID or PROVIDER!='gemini' or not os.environ.get('GEMINI_API_KEY'):
        raise SystemExit('Configure GOOGLE_CLIENT_ID, RELAY_PROVIDER=gemini and GEMINI_API_KEY.')
    # Fail startup instead of silently writing cloud campaigns to ephemeral disk.
    cloud.request('relay_records?select=kind&limit=0')

if __name__=='__main__':
    from waitress import serve
    validate()
    serve(application,host='0.0.0.0',port=int(os.environ.get('PORT','10000')),
          threads=4,connection_limit=100,max_request_body_size=4000000,
          channel_timeout=150,ident='Relay')
