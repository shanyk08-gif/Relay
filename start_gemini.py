"""Reuse a Gemini API key stored in macOS Keychain."""
import os
from pathlib import Path
import runpy
import socket
import sys
import subprocess

KEYCHAIN_ITEM = ['-s', 'Relay Gemini API', '-a', 'relay']


def saved_key():
    result = subprocess.run(
        ['/usr/bin/security', 'find-generic-password', *KEYCHAIN_ITEM, '-w'],
        capture_output=True, text=True,
    )
    if result.returncode == 44:  # Keychain item not found.
        return None
    if result.returncode:
        raise SystemExit('Could not access Relay’s Keychain entry. Unlock your login Keychain and retry.')
    key = result.stdout.strip()
    if not key or any(c.isspace() for c in key):
        raise SystemExit('Saved key is invalid. Delete “Relay Gemini API” in Keychain Access and restart.')
    return key


def load_key():
    key = saved_key()
    if key is None:
        print('One-time setup: paste your Gemini API key at the password prompt (input is hidden).', flush=True)
        print('Use a Free Tier Google project to avoid paid usage. Relay cannot verify your billing tier.', flush=True)
        # A trailing -w invokes Apple's private password prompt: no secret in argv or files.
        result = subprocess.run(['/usr/bin/security', 'add-generic-password', *KEYCHAIN_ITEM, '-w'])
        if result.returncode:
            raise SystemExit('Keychain save failed or was cancelled. Relay was not started.')
        key = saved_key()
        if key is None:
            raise SystemExit('The saved Keychain entry could not be found. Relay was not started.')
    return key


if __name__ == '__main__':
    runtime=Path(__file__).parent/'.venv/bin/python'
    if runtime.exists() and sys.prefix != str(runtime.parent.parent):
        os.execv(str(runtime),[str(runtime),str(Path(__file__).resolve())])
    with socket.socket() as probe:
        if probe.connect_ex(('127.0.0.1', 8154)) == 0:
            raise SystemExit('Relay already runs on port 8154. Stop its old Terminal with Ctrl+C, then run this launcher again.')
    os.environ['GEMINI_API_KEY'] = load_key()
    os.environ['RELAY_PROVIDER'] = 'gemini'
    print('Using Gemini key from macOS Keychain. Source text is sent to Google.')
    print('Keep this Terminal open. Open http://localhost:8154/')
    runpy.run_path(str(Path(__file__).with_name('server.py')), run_name='__main__')
