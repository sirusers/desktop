from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ClusterOut(BaseModel):
    id: int
    title: str
    size: int
    last_activity: Optional[datetime]
    created_at: datetime


class NewsOut(BaseModel):
    id: int
    title: str
    body: str
    published_at: Optional[datetime]
    source: Optional[str]
    hash_tags: List[str]
    fingerprint: Optional[str]
    cluster_id: Optional[int]
    created_at: datetime


class NewsCreate(BaseModel):
    title: str
    body: str
    published_at: Optional[datetime] = None
    source: Optional[str] = None
    hash_tags: List[str] = []
    cluster_id: Optional[int] = None


class GenerateNewsRequest(BaseModel):
    cluster_id: int
    prompt: str = ""


class GenerateNewsResponse(BaseModel):
    title: str
    body: str
