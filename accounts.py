"""Optional Google sign-in and per-account local workspaces (loopback deployment)."""
from contextlib import closing
import cloud
import hashlib
import json
import os
import secrets
import sqlite3
import threading
import time
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parent
CONFIG=ROOT/'google-client-id.txt'
CLIENT_ID=os.environ.get('GOOGLE_CLIENT_ID','').strip() or (CONFIG.read_text().strip() if CONFIG.exists() else '')
DB=ROOT/'data/accounts.sqlite3'
LOCK=threading.Lock()
SESSIONS={}
CHALLENGES={}
ATTEMPTS=[]
HOSTED=os.environ.get('RELAY_HOSTED')=='1'


def cookie(headers,name):
    try:
        # GIS g_state contains JSON that SimpleCookie rejects. Parse only our cookie.
        matches=[part.strip() for part in headers.get('Cookie','').split(';')
                 if part.partition('=')[0].strip()==name]
        if len(matches)!=1:return ''
        jar=SimpleCookie();jar.load(matches[0])
        return jar[name].value if name in jar else ''
    except Exception:return ''


def user(headers):
    token=cookie(headers,'relay_session')
    if HOSTED:
        row=cloud.get('session',hashlib.sha256(token.encode()).hexdigest()) if token else None
        return row['value']['sub'] if row and row['expires']>time.time() else None
    with LOCK:
        value=SESSIONS.get(hashlib.sha256(token.encode()).hexdigest())
        return value['sub'] if value and value['expires']>time.time() else None


def challenge():
    now=time.time()
    if HOSTED:
        if not cloud.limit('login-challenges',100,600):raise ValueError('Login is busy. Retry in a few minutes.')
        token,nonce=secrets.token_urlsafe(32),secrets.token_urlsafe(32)
        cloud.put('challenge',hashlib.sha256(token.encode()).hexdigest(),{'nonce':nonce},now+600)
        return token,nonce
    with LOCK:
        for key in list(CHALLENGES):
            if CHALLENGES[key]['expires']<now:del CHALLENGES[key]
        if len(CHALLENGES)>=100:raise ValueError('Too many login attempts. Wait a few minutes.')
        token,nonce=secrets.token_urlsafe(32),secrets.token_urlsafe(32)
        CHALLENGES[token]={'nonce':nonce,'expires':now+600}
    return token,nonce


def verify(credential):
    from google.oauth2 import id_token
    from google.auth.transport.requests import Request
    return id_token.verify_oauth2_token(credential,Request(),CLIENT_ID)


def login(headers,data):
    if not isinstance(data,dict) or not isinstance(data.get('credential'),str) or not 10<len(data['credential'])<10000:
        raise ValueError('Invalid sign-in response.')
    now=time.time()
    if HOSTED:
        if not cloud.limit('login-attempts',100,900):raise ValueError('Too many sign-in attempts. Try later.')
        row=cloud.remove('challenge',hashlib.sha256(cookie(headers,'relay_login').encode()).hexdigest())
        pending=dict(row['value'],expires=row['expires']) if row else None
    else:
        with LOCK:
            ATTEMPTS[:]=[t for t in ATTEMPTS if t>now-900]
            if len(ATTEMPTS)>=10:raise ValueError('Too many sign-in attempts. Try again in 15 minutes.')
            ATTEMPTS.append(now)
            pending=CHALLENGES.pop(cookie(headers,'relay_login'),None)
    if not pending or pending['expires']<now:raise ValueError('Sign-in expired. Reload the login page.')
    try:claims=verify(data['credential'])
    except Exception:raise ValueError('Google sign-in could not be verified. Reload and try again.') from None
    if not isinstance(claims.get('sub'),str) or not claims['sub'] or len(claims['sub'])>255 or not secrets.compare_digest(str(claims.get('nonce','')),pending['nonce']):
        raise ValueError('Google sign-in could not be verified.')
    token=secrets.token_urlsafe(32)
    if HOSTED:
        logout(headers)
        cloud.put('session',hashlib.sha256(token.encode()).hexdigest(),{'sub':claims['sub'],'profile':profile_claims(claims)},now+28800)
        return token
    with LOCK:
        for key in list(SESSIONS):
            if SESSIONS[key]['expires']<now:del SESSIONS[key]
        old=cookie(headers,'relay_session')
        SESSIONS.pop(hashlib.sha256(old.encode()).hexdigest(),None)
        SESSIONS[hashlib.sha256(token.encode()).hexdigest()]={'sub':claims['sub'],'expires':now+28800,'profile':profile_claims(claims)}
    return token


def profile_claims(claims):
    picture=claims.get('picture','')
    try:
        url=urlsplit(picture) if isinstance(picture,str) else None
        picture=picture if url and url.scheme=='https' and url.hostname and url.hostname.endswith('.googleusercontent.com') and not url.username and not url.password else ''
    except ValueError:picture=''
    return {'name':str(claims.get('name') or 'Google account')[:120],
            'email':str(claims.get('email') or '')[:254] if claims.get('email_verified') is True else '',
            'picture':picture[:2048]}


def profile(headers):
    if HOSTED:
        token=cookie(headers,'relay_session')
        row=cloud.get('session',hashlib.sha256(token.encode()).hexdigest()) if token else None
        return row['value'].get('profile',{}) if row and row['expires']>time.time() else {}
    with LOCK:
        session=SESSIONS.get(hashlib.sha256(cookie(headers,'relay_session').encode()).hexdigest(),{})
        return session.get('profile',{}) if session.get('expires',0)>time.time() else {}


def logout(headers):
    if HOSTED:
        token=cookie(headers,'relay_session')
        if token:cloud.remove('session',hashlib.sha256(token.encode()).hexdigest())
        return
    with LOCK:SESSIONS.pop(hashlib.sha256(cookie(headers,'relay_session').encode()).hexdigest(),None)


def database():
    DB.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    conn=sqlite3.connect(DB)
    os.chmod(DB,0o600)
    conn.execute('CREATE TABLE IF NOT EXISTS workspaces (owner TEXT PRIMARY KEY, content TEXT NOT NULL)')
    return conn


def workspace(owner,value=None):
    if value is not None:
        if not isinstance(value,list) or len(value)>200:raise ValueError('Workspace must contain at most 200 campaigns.')
        formats={'summary','advisory','linkedin','thread','slides','infographic','video'}
        for c in value:
            if not isinstance(c,dict) or not all(isinstance(c.get(k),str) for k in ('id','title','source','updated','audience','tone','language','detail','objective','active')) or c['active'] not in formats:
                raise ValueError('Invalid campaign data.')
            if not isinstance(c.get('drafts'),dict) or not all(isinstance(c['drafts'].get(k),dict) and isinstance(c['drafts'][k].get('text'),str) and isinstance(c['drafts'][k].get('reviewed'),bool) for k in formats):raise ValueError('Invalid draft data.')
        content=json.dumps(value,ensure_ascii=False)
        if len(content.encode())>4000000:raise ValueError('Workspace exceeds 4 MB. Export a backup and remove older versions.')
    if HOSTED:
        if value is not None:
            cloud.put('workspace',owner,value)
            return {'saved':True}
        row=cloud.get('workspace',owner)
        return row['value'] if row else []
    with closing(database()) as conn, conn:
        if value is not None:
            conn.execute('INSERT INTO workspaces VALUES (?,?) ON CONFLICT(owner) DO UPDATE SET content=excluded.content',(owner,content))
            return {'saved':True}
        row=conn.execute('SELECT content FROM workspaces WHERE owner=?',(owner,)).fetchone()
        return json.loads(row[0]) if row else []
