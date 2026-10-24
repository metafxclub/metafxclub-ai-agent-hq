"""Secrets encrypted by Windows DPAPI for the current Windows user only."""
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import threading


class _Blob(ctypes.Structure):
    _fields_ = [('size', wintypes.DWORD), ('data', ctypes.POINTER(ctypes.c_ubyte))]


def _crypt(raw, decrypt=False):
    if os.name != 'nt':
        raise RuntimeError('Windows DPAPI is required for credential storage')
    memory = ctypes.create_string_buffer(raw)
    source = _Blob(len(raw), ctypes.cast(memory, ctypes.POINTER(ctypes.c_ubyte)))
    target = _Blob()
    crypt = ctypes.windll.crypt32
    if decrypt:
        ok = crypt.CryptUnprotectData(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(target))
    else:
        ok = crypt.CryptProtectData(ctypes.byref(source), 'Metafxclub Sentiment Universe', None, None, None, 1, ctypes.byref(target))
    if not ok:
        raise RuntimeError('Credential encryption or decryption failed')
    try:
        return ctypes.string_at(target.data, target.size)
    finally:
        ctypes.windll.kernel32.LocalFree(target.data)


class SecretStore:
    def __init__(self, directory):
        self.path = Path(directory) / 'myfxbook.dpapi'
        self.lock = threading.RLock()

    def _read(self):
        if not self.path.exists():
            return {}
        return json.loads(_crypt(self.path.read_bytes(), decrypt=True))

    def _write(self, value):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix('.tmp')
        temporary.write_bytes(_crypt(json.dumps(value).encode('utf-8')))
        os.replace(temporary, self.path)

    def credentials(self):
        with self.lock:
            return self._read().get('credentials')

    def save_credentials(self, email, password):
        with self.lock:
            # Replacing credentials invalidates any previous account's session.
            self._write({'credentials': {'email': email, 'password': password}})

    def session(self):
        with self.lock:
            return self._read().get('session')

    def save_session(self, value):
        with self.lock:
            data = self._read()
            data['session'] = value
            self._write(data)

    def clear_session(self):
        with self.lock:
            data = self._read()
            data.pop('session', None)
            self._write(data)
