"""Helper utility functions."""
from typing import Optional
from app.db import get_session
from app.models import Audit
from sqlmodel import select


def get_latest_audit_id() -> Optional[int]:
    """Get the latest audit ID - lightweight query."""
    with get_session() as session:
        latest_audit = session.exec(select(Audit).order_by(Audit.id.desc()).limit(1)).first()
        return latest_audit.id if latest_audit else None

