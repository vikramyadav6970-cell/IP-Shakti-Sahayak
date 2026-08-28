"""
Audit log utility — append-only writes for DPDP compliance.
Import and call `write_audit_log` from any endpoint that touches
sensitive/substantive data.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLog
from typing import Any, Optional
from uuid import UUID


async def write_audit_log(
    db: AsyncSession,
    user_id: Optional[UUID],
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    metadata_payload: Optional[dict[str, Any]] = None,
) -> AuditLog:
    """
    Write an append-only audit log entry.

    Parameters
    ----------
    db : AsyncSession
    user_id : UUID | None — the acting user (None for system actions)
    action : str — e.g. "CHAT_QUERY", "CLASSIFICATION_CREATE", "EXPERT_REQUEST_CREATE"
    resource_type : str | None — e.g. "Conversation", "Classification", "ExpertRequest"
    resource_id : str | None — the PK of the affected resource
    metadata_payload : dict | None — extra context (question text, IP type, etc.)
    """
    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata_payload=metadata_payload,
    )
    db.add(entry)
    await db.flush()
    return entry
