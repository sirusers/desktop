from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional


@dataclass(frozen=True)
class Cluster:
    id: int
    name: str


@dataclass(frozen=True)
class NewsItem:
    id: int
    cluster_id: int
    title: str
    body: str
    created_at: datetime


class InMemoryRepository:
    def __init__(self) -> None:
        self._clusters: List[Cluster] = [
            Cluster(1, "Кластер 1"),
            Cluster(2, "Кластер 2"),
            Cluster(3, "Кластер 3"),
            Cluster(4, "Кластер 4"),
        ]
        self._news: Dict[int, List[NewsItem]] = {
            1: [
                NewsItem(1, 1, "Новость 1. Трамп назвал себя королем биткоина", "Текст новости 1...", datetime.now()),
                NewsItem(2, 1, "Новость 2. Биткоин упал до 66к после выступления", "Текст новости 2...", datetime.now()),
                NewsItem(3, 1, "Новость 3. Обвал биткоина на фоне заявления", "Текст новости 3...", datetime.now()),
            ],
            2: [
                NewsItem(10, 2, "Новость 1. Рынок отреагировал на заявление", "Детали новости…", datetime.now()),
                NewsItem(11, 2, "Новость 2. Волатильность усилилась", "Детали новости…", datetime.now()),
            ],
            3: [],
            4: [],
        }
        self._next_news_id = 1000
        self._by_id: Dict[int, NewsItem] = {}
        self._reindex()

    def _reindex(self) -> None:
        self._by_id.clear()
        for _, items in self._news.items():
            for it in items:
                self._by_id[it.id] = it

    def list_clusters(self) -> List[Cluster]:
        return list(self._clusters)

    def get_cluster(self, cluster_id: int) -> Optional[Cluster]:
        for c in self._clusters:
            if c.id == cluster_id:
                return c
        return None

    def list_news(self, cluster_id: int) -> List[NewsItem]:
        return list(self._news.get(cluster_id, []))

    def search_news(self, cluster_id: int, q: str) -> List[NewsItem]:
        items = self.list_news(cluster_id)
        q = (q or "").strip().lower()
        if not q:
            return items
        out: List[NewsItem] = []
        for it in items:
            if q in it.title.lower() or q in (it.body or "").lower():
                out.append(it)
        return out

    def get_news(self, news_id: int | None) -> Optional[NewsItem]:
        if not news_id:
            return None
        return self._by_id.get(news_id)

    def add_news(self, cluster_id: int, title: str, body: str) -> NewsItem:
        self._next_news_id += 1
        item = NewsItem(
            id=self._next_news_id,
            cluster_id=cluster_id,
            title=title,
            body=body,
            created_at=datetime.now(),
        )
        self._news.setdefault(cluster_id, []).insert(0, item)
        self._by_id[item.id] = item
        return item

    def delete_news(self, news_id: int) -> None:
        # удалить из списка кластера
        for cid, items in self._news.items():
            for i, it in enumerate(items):
                if it.id == news_id:
                    del items[i]
                    self._by_id.pop(news_id, None)
                    return
