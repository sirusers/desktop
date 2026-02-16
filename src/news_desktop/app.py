from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from news_desktop.news import router as news_router, db as backend_db
from news_desktop.api_models import NewsCreate, GenerateNewsRequest

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Подключаем API
app.include_router(news_router)


# ---------------- UI helpers (работаем по контракту БД) ----------------
def list_clusters():
    return backend_db.list_clusters()

def get_cluster(cluster_id: int):
    return backend_db.get_cluster(cluster_id)

def list_news(cluster_id: int, q: str):
    return backend_db.search_in_cluster(cluster_id, q)

def get_news(news_id: int):
    return backend_db.get_news(news_id)

def delete_news(news_id: int):
    backend_db.delete_news(news_id)

def save_news_one(data: NewsCreate):
    backend_db.create_news(data)

def generate_draft(req: GenerateNewsRequest):
    # вызываем ту же логику, что и /news/generate_news (draft)
    title = f"Сгенерировано для кластера {req.cluster_id}"
    prompt = (req.prompt or "").strip() or "Стандартный промпт"
    body = f"Промпт: {prompt}\n\nСгенерированный текст новости..."
    return {"title": title, "body": body}


def _render_page(
    request: Request,
    cluster_id: int,
    mode: str,
    q: str = "",
    selected_news_id: Optional[int] = None,
):
    clusters = list_clusters()
    if not clusters:
        return templates.TemplateResponse(
            "partials/page_list.html",
            {"request": request, "clusters": [], "cluster": None, "news": [], "selected_cluster_id": 0, "mode": mode, "q": q, "selected_news": None},
        )

    cluster = get_cluster(cluster_id) or clusters[0]
    cluster_id = cluster.id

    news = list_news(cluster_id, q)
    selected_news = get_news(selected_news_id) if selected_news_id else None
    if selected_news and selected_news.cluster_id != cluster_id:
        selected_news = None

    ctx = {
        "request": request,
        "clusters": clusters,
        "selected_cluster_id": cluster_id,
        "cluster": cluster,
        "news": news,
        "mode": mode,
        "q": q,
        "selected_news": selected_news,
    }

    tpl = "partials/page_generate.html" if mode == "generate" else "partials/page_list.html"
    return templates.TemplateResponse(tpl, ctx)


@app.get("/", response_class=HTMLResponse)
def index(request: Request, cluster_id: Optional[int] = None, mode: str = "list", q: str = ""):
    clusters = list_clusters()
    if clusters and cluster_id is None:
        cluster_id = clusters[0].id
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "clusters": clusters, "selected_cluster_id": cluster_id or 0, "mode": mode},
    )


@app.get("/page", response_class=HTMLResponse)
def page(request: Request, cluster_id: int, mode: str = "list", q: str = "", selected_news_id: Optional[int] = None):
    return _render_page(request, cluster_id=cluster_id, mode=mode, q=q, selected_news_id=selected_news_id)


@app.get("/clusters/{cluster_id}/news", response_class=HTMLResponse)
def news_list_partial(request: Request, cluster_id: int, mode: str = "list", q: str = ""):
    cluster = get_cluster(cluster_id)
    news = list_news(cluster_id, q)
    return templates.TemplateResponse(
        "partials/news_list.html",
        {"request": request, "cluster": cluster, "news": news, "selected_cluster_id": cluster_id, "mode": mode, "q": q},
    )


@app.get("/news/{news_id}/view", response_class=HTMLResponse)
def news_view(request: Request, news_id: int, cluster_id: int, mode: str = "list", q: str = ""):
    item = get_news(news_id)
    if item is None or item.cluster_id != cluster_id:
        item = None
    return templates.TemplateResponse(
        "partials/news_viewer.html",
        {"request": request, "selected_news": item, "cluster_id": cluster_id, "mode": mode, "q": q},
    )


@app.post("/clusters/{cluster_id}/news/add", response_class=HTMLResponse)
def add_news_ui(
    request: Request,
    cluster_id: int,
    mode: str = Form("list"),
    q: str = Form(""),
    title: str = Form(...),
    body: str = Form(""),
    source: str = Form("manual"),
):
    save_news_one(NewsCreate(title=title.strip(), body=body.strip(), source=source.strip() or "manual", cluster_id=cluster_id))
    return _render_page(request, cluster_id=cluster_id, mode=mode, q=q)


@app.post("/news/{news_id}/delete", response_class=HTMLResponse)
def delete_news_ui(
    request: Request,
    news_id: int,
    cluster_id: int = Form(...),
    mode: str = Form("list"),
    q: str = Form(""),
):
    delete_news(news_id)
    return _render_page(request, cluster_id=cluster_id, mode=mode, q=q)


@app.get("/clusters/{cluster_id}/generator_panel", response_class=HTMLResponse)
def generator_panel(request: Request, cluster_id: int, mode: str = "generate", q: str = ""):
    return templates.TemplateResponse(
        "partials/generator_panel.html",
        {"request": request, "cluster_id": cluster_id, "mode": mode, "q": q, "prompt": "", "draft": None},
    )


@app.post("/clusters/{cluster_id}/generate_draft", response_class=HTMLResponse)
def generate_draft_ui(
    request: Request,
    cluster_id: int,
    mode: str = Form("generate"),
    q: str = Form(""),
    prompt: str = Form(""),
):
    draft = generate_draft(GenerateNewsRequest(cluster_id=cluster_id, prompt=prompt))
    return templates.TemplateResponse(
        "partials/generator_panel.html",
        {"request": request, "cluster_id": cluster_id, "mode": mode, "q": q, "prompt": prompt, "draft": draft},
    )


@app.post("/clusters/{cluster_id}/news/add_generated", response_class=HTMLResponse)
def add_generated_ui(
    request: Request,
    cluster_id: int,
    mode: str = Form("generate"),
    q: str = Form(""),
    title: str = Form(...),
    body: str = Form(""),
):
    save_news_one(NewsCreate(title=title.strip(), body=body.strip(), source="generated", cluster_id=cluster_id))
    return _render_page(request, cluster_id=cluster_id, mode=mode, q=q)
