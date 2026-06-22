from __future__ import annotations

from cpos.context_store import ContextStore
from cpos.registry import ContextObject, ContextRegistry
from cpos.scheduler import Scheduler
from cpos.kernel import CPOS
from cpos.review_keys import MemoryReviewKeyStore, WindowsReviewKeyStore, credential_target
from cryptography.fernet import Fernet
import pytest


def make_scheduler() -> tuple[Scheduler, ContextRegistry]:
    registry = ContextRegistry()
    registry.register(
        ContextObject(
            id="ctx_report",
            type="draft",
            title="Report",
            summary="Local report",
            data="original",
        )
    )
    return Scheduler(ContextStore(registry)), registry


def test_submit_keeps_content_out_of_context_registry() -> None:
    scheduler, registry = make_scheduler()
    scheduler.set_agent("writer", pid=10)

    result = scheduler.submit_review_draft(
        "ctx_report",
        "quarantined content",
        ["ctx_ext", "ctx_local"],
        "fresh external chain",
    )

    assert result["status"] == "awaiting_review"
    assert registry.get("ctx_report").data == "original"
    draft = scheduler.review_drafts.get(result["review_id"])
    assert draft is not None
    assert draft.content == "quarantined content"
    assert draft.source_ids == ["ctx_ext", "ctx_local"]


def test_only_root_can_promote_reviewed_draft() -> None:
    scheduler, registry = make_scheduler()
    scheduler.set_agent("writer", pid=10)
    submitted = scheduler.submit_review_draft(
        "ctx_report", "new content", ["ctx_ext"], "fresh external chain"
    )

    denied = scheduler.approve_review_draft(submitted["review_id"])

    assert denied == {"status": "error", "result": "ERR_REVIEW_APPROVAL_DENIED"}
    assert registry.get("ctx_report").data == "original"

    scheduler.set_agent("root")
    approved = scheduler.approve_review_draft(submitted["review_id"])

    assert approved["status"] == "ok"
    target = registry.get("ctx_report")
    assert target.data == "new content"
    assert target.metadata["reviewed"] is True
    assert target.metadata["provenance_sources"] == ["ctx_ext"]


def test_rejected_draft_never_reaches_target() -> None:
    scheduler, registry = make_scheduler()
    submitted = scheduler.submit_review_draft(
        "ctx_report", "discard me", ["ctx_ext"], "failed review"
    )

    rejected = scheduler.reject_review_draft(submitted["review_id"])

    assert rejected["status"] == "ok"
    assert registry.get("ctx_report").data == "original"
    assert scheduler.review_drafts.get(submitted["review_id"]) is None
    assert scheduler.review_drafts.history[-1].status == "rejected"


def test_approval_can_create_missing_local_draft_target() -> None:
    scheduler = Scheduler(ContextStore(ContextRegistry()))
    submitted = scheduler.submit_review_draft(
        "ctx_new_report", "new report", ["ctx_ext"], "fresh external chain"
    )

    approved = scheduler.approve_review_draft(submitted["review_id"])

    assert approved["status"] == "ok"
    target = scheduler.registry.get("ctx_new_report")
    assert target is not None
    assert target.type == "draft"
    assert target.data == "new report"


def test_cpos_exposes_review_transition_api(tmp_path) -> None:
    cpos = CPOS(workspace=str(tmp_path))

    submitted = cpos.submit_review_draft(
        "ctx_runtime_report",
        "runtime draft",
        ["ctx_ext"],
        "fresh import chain",
        agent="writer",
        pid=12,
    )
    denied = cpos.approve_review_draft(submitted["review_id"], agent="writer")
    approved = cpos.approve_review_draft(submitted["review_id"], agent="root")

    assert denied["result"] == "ERR_REVIEW_APPROVAL_DENIED"
    assert approved["result"] == "REVIEW_PROMOTED"
    assert cpos.registry.get("ctx_runtime_report").data == "runtime draft"


def test_encrypted_review_store_recovers_after_restart(tmp_path) -> None:
    key = Fernet.generate_key().decode("ascii")
    first = CPOS(workspace=str(tmp_path), review_encryption_key=key)
    submitted = first.submit_review_draft(
        "ctx_recovered_report",
        "secret quarantined draft",
        ["ctx_ext"],
        "restart recovery",
        agent="writer",
    )
    encrypted_path = tmp_path / ".cpos" / "review_drafts.enc"

    assert encrypted_path.exists()
    assert b"secret quarantined draft" not in encrypted_path.read_bytes()
    assert first.registry.get("ctx_recovered_report") is None

    recovered = CPOS(workspace=str(tmp_path), review_encryption_key=key)
    pending = recovered.scheduler.review_drafts.get(submitted["review_id"])
    assert pending is not None
    assert pending.content == "secret quarantined draft"

    approved = recovered.approve_review_draft(submitted["review_id"], agent="root")
    assert approved["status"] == "ok"
    assert recovered.registry.get("ctx_recovered_report").data == "secret quarantined draft"
    assert recovered.scheduler.review_drafts.history[-1].content == ""

    restarted = CPOS(workspace=str(tmp_path), review_encryption_key=key)
    assert restarted.scheduler.review_drafts.get(submitted["review_id"]) is None
    assert restarted.scheduler.review_drafts.history[-1].status == "approved"
    assert restarted.scheduler.review_drafts.history[-1].content == ""


def test_encrypted_review_store_rejects_wrong_key_or_tampering(tmp_path) -> None:
    key = Fernet.generate_key().decode("ascii")
    cpos = CPOS(workspace=str(tmp_path), review_encryption_key=key)
    cpos.submit_review_draft("ctx_report", "private", ["ctx_ext"], "test")

    with pytest.raises(ValueError, match="authenticated or decrypted"):
        CPOS(
            workspace=str(tmp_path),
            review_encryption_key=Fernet.generate_key().decode("ascii"),
        )

    encrypted_path = tmp_path / ".cpos" / "review_drafts.enc"
    token = bytearray(encrypted_path.read_bytes())
    token[-1] = ord("A") if token[-1] != ord("A") else ord("B")
    encrypted_path.write_bytes(bytes(token))

    with pytest.raises(ValueError, match="authenticated or decrypted"):
        CPOS(workspace=str(tmp_path), review_encryption_key=key)


def test_os_key_store_provisions_recovers_and_rotates(tmp_path) -> None:
    key_store = MemoryReviewKeyStore()
    first = CPOS(
        workspace=str(tmp_path),
        review_credential_id="primary",
        create_review_credential=True,
        review_key_store=key_store,
    )
    submitted = first.submit_review_draft(
        "ctx_rotated", "rotating draft", ["ctx_ext"], "rotation test", agent="writer"
    )
    target = credential_target(str(tmp_path), "primary")
    old_key = key_store.get_keys(target)[0]

    rotated = first.rotate_review_encryption_key(agent="root")

    assert rotated == {"status": "ok", "result": "REVIEW_KEY_ROTATED"}
    assert key_store.get_keys(target)[0] != old_key
    recovered = CPOS(
        workspace=str(tmp_path),
        review_credential_id="primary",
        review_key_store=key_store,
    )
    assert recovered.scheduler.review_drafts.get(submitted["review_id"]).content == "rotating draft"


def test_interrupted_rotation_uses_previous_key_and_self_heals(tmp_path) -> None:
    key_store = MemoryReviewKeyStore()
    first = CPOS(
        workspace=str(tmp_path),
        review_credential_id="primary",
        create_review_credential=True,
        review_key_store=key_store,
    )
    first.submit_review_draft("ctx_report", "recover me", ["ctx_ext"], "crash test")
    target = credential_target(str(tmp_path), "primary")
    old_key = key_store.get_keys(target)[0]
    new_key = Fernet.generate_key().decode("ascii")
    key_store.begin_rotation(target, new_key, old_key)

    recovered = CPOS(
        workspace=str(tmp_path),
        review_credential_id="primary",
        review_key_store=key_store,
    )

    assert recovered.scheduler.review_drafts.get("review_1").content == "recover me"
    # Loading through the previous key rewrites ciphertext under the current key.
    CPOS(workspace=str(tmp_path), review_encryption_key=new_key)


def test_review_key_rotation_requires_root_and_rolls_back_on_failure(tmp_path, monkeypatch) -> None:
    key_store = MemoryReviewKeyStore()
    cpos = CPOS(
        workspace=str(tmp_path),
        review_credential_id="primary",
        create_review_credential=True,
        review_key_store=key_store,
    )
    cpos.submit_review_draft("ctx_report", "content", ["ctx_ext"], "test")
    target = credential_target(str(tmp_path), "primary")
    old_key = key_store.get_keys(target)[0]

    denied = cpos.rotate_review_encryption_key(agent="writer")
    assert denied["result"] == "ERR_REVIEW_ROTATION_DENIED"

    def fail_rotation(new_key: str) -> None:
        raise OSError("disk failure")

    monkeypatch.setattr(cpos.scheduler.review_drafts, "rotate_encryption_key", fail_rotation)
    with pytest.raises(OSError, match="disk failure"):
        cpos.rotate_review_encryption_key(agent="root")

    assert key_store.get_keys(target) == [old_key]


def test_windows_key_payload_and_not_found_detection() -> None:
    current = Fernet.generate_key().decode("ascii")
    previous = Fernet.generate_key().decode("ascii")
    payload = '{"current":"%s","previous":"%s"}' % (current, previous)

    assert WindowsReviewKeyStore._decode_payload(payload) == [current, previous]
    assert WindowsReviewKeyStore._is_not_found(Exception(1168, "missing")) is True
    assert WindowsReviewKeyStore._is_not_found(Exception(5, "denied")) is False


def test_create_os_key_requires_credential_id(tmp_path) -> None:
    with pytest.raises(ValueError, match="requires review_credential_id"):
        CPOS(workspace=str(tmp_path), create_review_credential=True)
