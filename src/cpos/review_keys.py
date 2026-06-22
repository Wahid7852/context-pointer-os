from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional

from cryptography.fernet import Fernet


def credential_target(workspace: str, credential_id: str) -> str:
    workspace_hash = hashlib.sha256(str(Path(workspace).resolve()).encode("utf-8")).hexdigest()[:24]
    return f"CPOS/ReviewDraft/{credential_id}/{workspace_hash}"


class WindowsReviewKeyStore:
    """Stores review keys in the current user's Windows Credential Manager."""

    username = "cpos-review-draft"

    def _module(self):
        try:
            import win32cred
        except ImportError as exc:
            raise RuntimeError("Windows Credential Manager requires pywin32") from exc
        return win32cred

    def get_keys(self, target: str) -> List[str]:
        win32cred = self._module()
        try:
            credential = win32cred.CredRead(target, win32cred.CRED_TYPE_GENERIC, 0)
        except Exception as exc:
            if self._is_not_found(exc):
                return []
            raise
        blob = credential.get("CredentialBlob", b"")
        raw = blob.decode("utf-16-le") if isinstance(blob, bytes) else str(blob)
        return self._decode_payload(raw)

    def provision(self, target: str, key: Optional[str] = None) -> str:
        if self.get_keys(target):
            raise ValueError("review credential already exists")
        current = key or Fernet.generate_key().decode("ascii")
        self._write(target, {"current": current})
        return current

    def begin_rotation(self, target: str, new_key: str, old_key: str) -> None:
        self._write(target, {"current": new_key, "previous": old_key})

    def finalize_rotation(self, target: str, new_key: str) -> None:
        self._write(target, {"current": new_key})

    def restore(self, target: str, old_key: str) -> None:
        self._write(target, {"current": old_key})

    def delete(self, target: str) -> None:
        win32cred = self._module()
        try:
            win32cred.CredDelete(target, win32cred.CRED_TYPE_GENERIC, 0)
        except Exception as exc:
            if not self._is_not_found(exc):
                raise

    def _write(self, target: str, payload: Dict[str, str]) -> None:
        win32cred = self._module()
        win32cred.CredWrite(
            {
                "Type": win32cred.CRED_TYPE_GENERIC,
                "TargetName": target,
                "UserName": self.username,
                "CredentialBlob": json.dumps(payload, sort_keys=True),
                "Persist": win32cred.CRED_PERSIST_LOCAL_MACHINE,
                "Comment": "CPOS encrypted review draft key",
            },
            0,
        )

    @staticmethod
    def _decode_payload(raw: str) -> List[str]:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return [raw] if raw else []
        keys = [payload.get("current"), payload.get("previous")]
        return [str(key) for key in keys if key]

    @staticmethod
    def _is_not_found(exc: Exception) -> bool:
        code = getattr(exc, "winerror", None)
        if code is None and getattr(exc, "args", None):
            code = exc.args[0]
        return code == 1168


class MemoryReviewKeyStore:
    """Test backend implementing the Windows key-store transaction contract."""

    def __init__(self) -> None:
        self.credentials: Dict[str, Dict[str, str]] = {}

    def get_keys(self, target: str) -> List[str]:
        payload = self.credentials.get(target, {})
        return [key for key in (payload.get("current"), payload.get("previous")) if key]

    def provision(self, target: str, key: Optional[str] = None) -> str:
        if target in self.credentials:
            raise ValueError("review credential already exists")
        current = key or Fernet.generate_key().decode("ascii")
        self.credentials[target] = {"current": current}
        return current

    def begin_rotation(self, target: str, new_key: str, old_key: str) -> None:
        self.credentials[target] = {"current": new_key, "previous": old_key}

    def finalize_rotation(self, target: str, new_key: str) -> None:
        self.credentials[target] = {"current": new_key}

    def restore(self, target: str, old_key: str) -> None:
        self.credentials[target] = {"current": old_key}

    def delete(self, target: str) -> None:
        self.credentials.pop(target, None)
