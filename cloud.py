"""Server-only Supabase storage. No credentials or database access in the browser."""
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

URL=os.environ.get('SUPABASE_URL','').rstrip('/')
KEY=os.environ.get('SUPABASE_SECRET_KEY','')

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        raise OSError('Unexpected database redirect.')


def request(path,method='GET',data=None,prefer='return=representation'):
    if not re.fullmatch(r'https://[a-z0-9]+\.supabase\.co',URL) or not KEY:
        raise OSError('Cloud storage is not configured.')
    headers={'apikey':KEY,'Content-Type':'application/json','Prefer':prefer}
    if not KEY.startswith('sb_secret_'):headers['Authorization']='Bearer '+KEY
    req=urllib.request.Request(URL+'/rest/v1/'+path,method=method,headers=headers,
                               data=json.dumps(data).encode() if data is not None else None)
    try:
        with urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect()).open(req,timeout=15) as response:
            raw=response.read(4500001)
            if len(raw)>4500000:raise OSError('Cloud response too large.')
            return json.loads(raw) if raw else None
    except (OSError,ValueError):raise OSError('Cloud storage is temporarily unavailable. Please retry.') from None


def get(kind,key):
    rows=request('relay_records?'+urllib.parse.urlencode({'kind':'eq.'+kind,'key':'eq.'+key,'select':'value,expires'}))
    return rows[0] if rows else None


def put(kind,key,value,expires=None):
    request('relay_records?on_conflict=kind,key','POST',{'kind':kind,'key':key,'value':value,'expires':expires},'resolution=merge-duplicates,return=minimal')


def remove(kind,key):
    # DELETE RETURNING consumes a login challenge exactly once, even across workers.
    rows=request('relay_records?'+urllib.parse.urlencode({'kind':'eq.'+kind,'key':'eq.'+key}),'DELETE')
    return rows[0] if rows else None


def limit(key,maximum,seconds):
    return request('rpc/relay_take_quota','POST',{'bucket':key,'maximum':maximum,'seconds':seconds}) is True
