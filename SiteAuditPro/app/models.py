from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON
from datetime import datetime
from typing import Optional, Dict, Any


class Audit(SQLModel, table=True):
    """Audit model for storing website analysis results."""
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str = Field(index=True)
    timestamp: datetime = Field(default_factory=datetime.now)
    title: Optional[str] = None
    score_seo: int = Field(default=0)
    score_performance: int = Field(default=0)
    score_security: int = Field(default=0)
    broken_links: int = Field(default=0)
    results_data: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    status: str = Field(default="pending")  # pending, processing, completed, failed

