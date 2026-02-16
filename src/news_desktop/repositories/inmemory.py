from __future__ import annotations

from datetime import datetime, UTC
from typing import Dict, List, Optional

from news_desktop.api_models import ClusterOut, NewsCreate, NewsOut


class InMemoryDB:
    def __init__(self) -> None:
        self._clusters: Dict[int, ClusterOut] = {}
        self._news: Dict[int, NewsOut] = {}
        self._cluster_id = 1
        self._news_id = 1
        self._seed()

    def _now(self) -> datetime:
        return datetime.now(UTC)

    def _seed(self) -> None:
        c1 = self.create_cluster("Трамп и крипта")
        c2 = self.create_cluster("Рынки")

        self.create_news(NewsCreate(
            title="Трамп назвал себя королем биткоина",
            body="Текст новости...",
            source="twitter",
            cluster_id=c1.id,
        ))
        self.create_news(NewsCreate(
            title="Биткоин упал после заявления",
            body="Подробный текст...",
            source="reuters",
            cluster_id=c1.id,
        ))
        self.create_news(NewsCreate(
            title="Волатильность усилилась",
            body="Детали новости…",
            source="bloomberg",
            cluster_id=c2.id,
        ))

    # -------- clusters --------
    def create_cluster(self, title: str) -> ClusterOut:
        now = self._now()
        cluster = ClusterOut(
            id=self._cluster_id,
            title=title,
            size=0,
            last_activity=None,
            created_at=now,
        )
        self._clusters[self._cluster_id] = cluster
        self._cluster_id += 1
        return cluster

    def list_clusters(self) -> List[ClusterOut]:
        return sorted(self._clusters.values(), key=lambda c: c.id)

    def get_cluster(self, cluster_id: int) -> Optional[ClusterOut]:
        return self._clusters.get(cluster_id)

    # -------- news --------
    def list_news(self, cluster_id: Optional[int] = None) -> List[NewsOut]:
        items = list(self._news.values())
        if cluster_id is not None:
            items = [n for n in items if n.cluster_id == cluster_id]
        return sorted(items, key=lambda n: n.id, reverse=True)

    def search_in_cluster(self, cluster_id: int, q: str) -> List[NewsOut]:
        items = self.list_news(cluster_id)
        qq = (q or "").strip().lower()
        if not qq:
            return items
        return [
            n for n in items
            if qq in n.title.lower()
            or qq in (n.body or "").lower()
            or qq in (n.source or "").lower()
        ]

    def get_news(self, news_id: int) -> Optional[NewsOut]:
        return self._news.get(news_id)

    def create_news(self, data: NewsCreate) -> NewsOut:
        now = self._now()
        item = NewsOut(
            id=self._news_id,
            title=data.title,
            body=data.body,
            published_at=data.published_at,
            source=data.source,
            hash_tags=data.hash_tags,
            fingerprint=None,
            cluster_id=data.cluster_id,
            created_at=now,
        )
        self._news[self._news_id] = item
        self._news_id += 1

        if data.cluster_id and data.cluster_id in self._clusters:
            cl = self._clusters[data.cluster_id]
            cl.size += 1
            cl.last_activity = now

        return item

    def delete_news(self, news_id: int) -> None:
        item = self._news.pop(news_id, None)
        if item and item.cluster_id and item.cluster_id in self._clusters:
            cl = self._clusters[item.cluster_id]
            cl.size = max(0, cl.size - 1)
