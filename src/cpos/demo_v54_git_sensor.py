import os
import json
import hashlib

from cpos.kernel import CPOS

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def git_fingerprint(repo_root: str) -> str:
    """Content hash of the whole .git directory, used as a read-only proof."""
    h = hashlib.sha256()
    git_dir = os.path.join(repo_root, ".git")
    for root, _dirs, files in sorted(os.walk(git_dir)):
        for name in sorted(files):
            full = os.path.join(root, name)
            h.update(os.path.relpath(full, git_dir).encode())
            try:
                with open(full, "rb") as f:
                    h.update(f.read())
            except OSError:
                continue
    return h.hexdigest()


def main():
    print("================================================")
    print("   CONTEXT POINTER OS - Phase 1 Read-Only Git Sensor")
    print("================================================")

    workspace = "/tmp/cpos_v54"
    os.makedirs(workspace, exist_ok=True)

    before = git_fingerprint(REPO_ROOT)
    print(f"\n.git fingerprint before: {before[:16]}...")

    os_kernel = CPOS(workspace=workspace, node_id="git-sensor-node")

    # The sensor is inert until a repository is explicitly registered. Paths
    # never come from the pointer string.
    os_kernel.gateways.gateways["git"].add_repo("self", REPO_ROOT)

    print("\n[Scenario: Mounting the repository as a read-only sensor pointer]")
    os_kernel.step(">MEM:LOAD #ptr://ext.git/self !5", agent="root")

    obj = os_kernel.registry.registry.get("git_self")
    if not obj:
        print("Sensor did not mount. Is this a git work tree?")
        return

    print("\nStructural observation:")
    print(json.dumps(json.loads(obj.data), indent=2, sort_keys=True))

    print("\nProvenance posture:")
    print(f"  source           : {obj.source}")
    print(f"  trust_score      : {obj.trust_score}  (exec gate needs >= 1.0)")
    print(f"  sensitivity      : {obj.sensitivity_level}")
    print(f"  untrusted_text   : {obj.metadata['untrusted_text']}")
    print("  quarantined text : "
          + json.dumps(obj.metadata["untrusted"], sort_keys=True))

    print("\n[Scenario: Autonomous re-sampling]")
    os_kernel.step(">SEC:MODE #ctx0 !9 | mode=autonomous", agent="root")
    for i in range(3):
        os_kernel.step(">MEM:LS #ctx0 !1", agent="root")
        snap = json.loads(os_kernel.registry.registry["git_self"].data)
        print(f"  tick {i + 1}: branch={snap['branch']} head={snap['head_short']} "
              f"dirty={snap['dirty']} ({snap['dirty_count']} paths)")

    print("\n[Scenario: Git observation cannot authorize execution]")
    os_kernel.scheduler.retrieval_policy.real_world_exec_enabled = True
    print(f"  EXEC on git_self -> {os_kernel.step('>REA:EXEC #git_self !5', agent='root')}")

    print("\nEmitted sensor events (kernel event log):")
    for entry in os_kernel.registry.audit_log:
        if str(entry.get("event", "")).startswith("git_sensor"):
            print(f"  {entry['event']:18} {entry.get('pointer_id')} "
                  f"{ {k: v for k, v in entry.items() if k not in ('event', 'pointer_id', 'timestamp')} }")

    after = git_fingerprint(REPO_ROOT)
    print(f"\n.git fingerprint after : {after[:16]}...")
    print(f"READ-ONLY {'CONFIRMED' if before == after else 'VIOLATED'}")


if __name__ == "__main__":
    main()
