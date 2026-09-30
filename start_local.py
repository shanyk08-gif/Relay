"""Start the project-local Ollama runtime and Relay. Ctrl+C stops owned processes."""
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

ROOT=Path(__file__).resolve().parent
RUNTIME=ROOT.parent.parent/'work'/'ollama-runtime'
BINARY=RUNTIME/'Ollama.app'/'Contents'/'Resources'/'ollama'

def running(port,path):
    try:
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(f'http://127.0.0.1:{port}{path}',timeout=2):return True
    except OSError:return False

if __name__=='__main__':
    runtime=ROOT/'.venv/bin/python'
    if runtime.exists() and sys.prefix != str(runtime.parent.parent):
        os.execv(str(runtime),[str(runtime),str(Path(__file__).resolve())])
    children=[]
    try:
        if not running(11434,'/api/tags'):
            if not BINARY.exists():sys.exit('Project-local Ollama is missing. See README.md for setup.')
            env=os.environ|{'OLLAMA_HOST':'127.0.0.1:11434','OLLAMA_NO_CLOUD':'1','OLLAMA_MODELS':str(RUNTIME/'models')}
            children.append(subprocess.Popen([str(BINARY),'serve'],env=env))
            for _ in range(30):
                if running(11434,'/api/tags'):break
                if children[0].poll() is not None:sys.exit('Ollama failed to start.')
                time.sleep(1)
            else:sys.exit('Ollama did not become ready.')
        if not running(8154,'/api/session'):
            children.append(subprocess.Popen([sys.executable,str(ROOT/'server.py')]))
        print('Open http://127.0.0.1:8154/ — keep this terminal open. Ctrl+C stops processes started here.',flush=True)
        while children:
            if any(p.poll() is not None for p in children):sys.exit('A local service stopped. Check the messages above.')
            time.sleep(1)
    except KeyboardInterrupt:pass
    finally:
        for process in children:
            if process.poll() is None:process.terminate()
        for process in children:
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:process.kill();process.wait()
