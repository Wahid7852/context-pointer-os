import pytest
from src.cpos.acl import AccessControlList, Role

def test_acl_roles():
    acl = AccessControlList()
    acl.set_role("admin", Role.ROOT)
    acl.set_role("guest_user", Role.GUEST)
    
    assert acl.get_role("admin") == Role.ROOT
    assert acl.get_role("guest_user") == Role.GUEST
    assert acl.get_role("unknown") == Role.GUEST # Verified: Default is GUEST in src/cpos/acl.py

def test_acl_check_root():
    acl = AccessControlList()
    # admin doesn't have ROOT role yet, but check handles 'root' agent name or ROOT role
    assert acl.check("root", "ctx1", "memory") is True
    
    acl.set_role("admin", Role.ROOT)
    assert acl.check("admin", "ctx1", "any") is True

def test_acl_check_guest_restrictions():
    acl = AccessControlList()
    acl.set_role("guest", Role.GUEST)
    
    # Sensitive types restricted for GUEST
    assert acl.check("guest", "ctx7", "neurostate") is False
    assert acl.check("guest", "ctx1", "memory") is False # No permission granted

def test_acl_grant():
    acl = AccessControlList()
    acl.set_role("user1", Role.USER)
    acl.grant("user1", "ctx1")
    assert acl.check("user1", "ctx1", "memory") is True
    assert acl.check("user1", "ctx2", "memory") is False

def test_acl_grant_type():
    acl = AccessControlList()
    acl.set_role("user1", Role.USER)
    acl.grant_type("user1", "log")
    assert acl.check("user1", "ctx_log_1", "log") is True
    assert acl.check("user1", "ctx1", "memory") is False
