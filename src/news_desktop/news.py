from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Query

from news_desktop.api_models import (
    ClusterOut, NewsCreate, NewsOut,
    GenerateNewsRequest, GenerateNewsResponse
)
from news_desktop.repositories.inmemory import InMemoryDB

router = APIRouter(prefix="/news", tags=["news"])
db = InMemoryDB()


@router.get("/get_cluster_list", response_model=List[ClusterOut])
def get_cluster_list():
    return db.list_clusters()


@router.get("/get_cluster_info", response_model=List[NewsOut])
def get_cluster_info(cluster_id: int = Query(...)):
    return db.list_news(cluster_id)


@router.get("/get_all_news", response_model=List[NewsOut])
def get_all_news():
    return db.list_news(None)


@router.get("/find_news", response_model=List[NewsOut])
def find_news(q: str = Query(...), cluster_id: Optional[int] = Query(None)):
    if cluster_id is None:
        # поиск по всем (в MVP можно вернуть просто get_all)
        qq = (q or "").strip().lower()
        return [n for n in db.list_news(None) if qq in n.title.lower() or qq in (n.source or "").lower()]
    return db.search_in_cluster(cluster_id, q)


@router.get("/find_news_by_content", response_model=List[NewsOut])
def find_news_by_content(q: str = Query(...), cluster_id: Optional[int] = Query(None)):
    qq = (q or "").strip().lower()
    items = db.list_news(cluster_id)
    return [n for n in items if qq in (n.body or "").lower()]


@router.post("/save_news")
def save_news(news_list: List[NewsCreate]):
    for n in news_list:
        db.create_news(n)
    return {"status": "ok", "saved": len(news_list)}


@router.post("/generate_news", response_model=GenerateNewsResponse)
def generate_news(payload: GenerateNewsRequest):
    # draft (не сохраняем)
    title = f"Сгенерировано для кластера {payload.cluster_id}"
    prompt = (payload.prompt or "").strip() or "Стандартный промпт"
    body = f"Промпт: {prompt}\n\nСгенерированный текст новости..."
    return GenerateNewsResponse(title=title, body=body)


@router.delete("/delete_news")
def delete_news(news_id: int = Query(...)):
    db.delete_news(news_id)
    return {"status": "ok", "deleted": news_id}
