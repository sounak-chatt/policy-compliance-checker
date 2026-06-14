"""Minimal RBAC. Roles: uploader, reviewer, admin. The role is read from
an X-Role header (demo simplicity). In production this comes from a JWT."""
from fastapi import Header, HTTPException

ROLE_PERMISSIONS = {
    "admin":    {"upload", "view", "audit", "manage"},
    "auditor":  {"upload", "view", "audit"},
    "manager":  {"view", "audit"},
    "viewer":   {"view"},
}


def require(permission: str):
    def _dep(x_role: str = Header(default="viewer")):
        role = (x_role or "viewer").lower()
        if role not in ROLE_PERMISSIONS:
            raise HTTPException(status_code=403, detail=f"Unknown role: {role}")
        if permission not in ROLE_PERMISSIONS[role]:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{role}' lacks '{permission}' permission")
        return role
    return _dep
