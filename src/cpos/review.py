from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Literal, Optional, Union

from cryptography.fernet import Fernet, InvalidToken
from pydantic import BaseModel, Field

from .registry import ContextObject, ContextRegistry


class ReviewDraft(BaseModel):
    id: str
    agent: str
    target_id: str
    content: str
    source_ids: List[str] = Field(default_factory=list)
    reason: str
    status: Literal["pending", "approved", "rejected"] = "pending"
    created_at: datetime = Field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None


class ReviewDraftStore:
    """Holds local drafts outside the active context registry until reviewed."""

    def __init__(
        self,
        persistence_path: Optional[Path] = None,
        encryption_key: Optional[Union[str, List[str]]] = None,
    ) -> None:
        if bool(persistence_path) != bool(encryption_key):
            raise ValueError("persistence_path and encryption_key must be configured together")
        self.pending: Dict[str, ReviewDraft] = {}
        self.history: List[ReviewDraft] = []
        self._next_id = 1
        self.persistence_path = persistence_path
        keys = [encryption_key] if isinstance(encryption_key, str) else list(encryption_key or [])
        self._fernets = [Fernet(key.encode("ascii")) for key in keys]
        self._fernet = self._fernets[0] if self._fernets else None
        if self.persistence_path and self.persistence_path.exists():
            self._load()

    @classmethod
    def for_workspace(
        cls,
        workspace: str,
        encryption_key: Union[str, List[str]],
    ) -> "ReviewDraftStore":
        return cls(Path(workspace) / ".cpos" / "review_drafts.enc", encryption_key)

    def rotate_encryption_key(self, new_key: str) -> None:
        if not self.persistence_path or not self._fernet:
            raise ValueError("encrypted persistence is not configured")
        old_fernet = self._fernet
        old_fernets = self._fernets
        try:
            self._fernet = Fernet(new_key.encode("ascii"))
            self._fernets = [self._fernet]
            self._persist()
        except Exception:
            self._fernet = old_fernet
            self._fernets = old_fernets
            raise

    def submit(
        self,
        agent: str,
        target_id: str,
        content: str,
        source_ids: List[str],
        reason: str,
    ) -> ReviewDraft:
        review_id = f"review_{self._next_id}"
        self._next_id += 1
        draft = ReviewDraft(
            id=review_id,
            agent=agent,
            target_id=target_id,
            content=content,
            source_ids=list(dict.fromkeys(source_ids)),
            reason=reason,
        )
        self.pending[review_id] = draft
        self._persist()
        return draft

    def get(self, review_id: str) -> Optional[ReviewDraft]:
        return self.pending.get(review_id)

    def approve(self, review_id: str, registry: ContextRegistry) -> Optional[ReviewDraft]:
        draft = self.pending.pop(review_id, None)
        if not draft:
            return None
        target = registry.get(draft.target_id)
        if not target:
            target = ContextObject(
                id=draft.target_id,
                type="draft",
                title="Reviewed Local Draft",
                summary="Content promoted from isolated review storage",
                source="review_quarantine",
                trust_score=0.5,
                sensitivity_level="internal",
            )
            registry.register(target)
        target.data = draft.content
        target.state.dirty = True
        target.metadata["review_id"] = draft.id
        target.metadata["reviewed"] = True
        target.metadata["provenance_sources"] = list(draft.source_ids)
        target.metadata["review_reason"] = draft.reason
        draft.content = ""
        draft.status = "approved"
        draft.resolved_at = datetime.now()
        self.history.append(draft)
        self._persist()
        return draft

    def reject(self, review_id: str) -> Optional[ReviewDraft]:
        draft = self.pending.pop(review_id, None)
        if not draft:
            return None
        draft.content = ""
        draft.status = "rejected"
        draft.resolved_at = datetime.now()
        self.history.append(draft)
        self._persist()
        return draft

    def _serialize_draft(self, draft: ReviewDraft) -> dict:
        if hasattr(draft, "model_dump"):
            return draft.model_dump(mode="json")
        return json.loads(draft.json())

    def _persist(self) -> None:
        if not self.persistence_path or not self._fernet:
            return
        payload = {
            "version": 1,
            "next_id": self._next_id,
            "pending": [self._serialize_draft(draft) for draft in self.pending.values()],
            "history": [self._serialize_draft(draft) for draft in self.history],
        }
        ciphertext = self._fernet.encrypt(
            json.dumps(payload, ensure_ascii=True, sort_keys=True).encode("utf-8")
        )
        self.persistence_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.persistence_path.with_suffix(self.persistence_path.suffix + ".tmp")
        temp_path.write_bytes(ciphertext)
        try:
            os.chmod(temp_path, 0o600)
        except OSError:
            pass
        os.replace(temp_path, self.persistence_path)

    def _load(self) -> None:
        if not self.persistence_path or not self._fernet:
            return
        ciphertext = self.persistence_path.read_bytes()
        plaintext = None
        used_fallback = False
        for index, fernet in enumerate(self._fernets):
            try:
                plaintext = fernet.decrypt(ciphertext)
                used_fallback = index > 0
                break
            except InvalidToken:
                continue
        if plaintext is None:
            raise ValueError("review draft storage could not be authenticated or decrypted")
        try:
            payload = json.loads(plaintext.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValueError("review draft storage could not be authenticated or decrypted") from exc
        if payload.get("version") != 1:
            raise ValueError("unsupported review draft storage version")
        pending = [ReviewDraft(**item) for item in payload.get("pending", [])]
        history = [ReviewDraft(**item) for item in payload.get("history", [])]
        self.pending = {draft.id: draft for draft in pending}
        self.history = history
        self._next_id = max(
            int(payload.get("next_id", 1)),
            1 + max((self._numeric_id(draft.id) for draft in [*pending, *history]), default=0),
        )
        if used_fallback:
            self._persist()

    @staticmethod
    def _numeric_id(review_id: str) -> int:
        try:
            return int(review_id.rsplit("_", 1)[1])
        except (IndexError, ValueError):
            return 0
