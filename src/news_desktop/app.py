from pathlib import Path
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from news_desktop.services.repository import InMemoryRepository
from news_desktop.services.generator import NewsGeneratorService

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

repo = InMemoryRepository()
gen = NewsGeneratorService()


def _render_page(request: Request, cluster_id: int, mode: str, q: str = "", selected_news_id: int | None = None):
    clusters = repo.list_clusters()
    cluster = repo.get_cluster(cluster_id) if clusters else None
    if cluster is None and clusters:
        cluster = clusters[0]
        cluster_id = cluster.id

    news = repo.search_news(cluster_id, q) if cluster else []
    selected_news = repo.get_news(selected_news_id) if selected_news_id else None
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
def index(request: Request, cluster_id: int | None = None, mode: str = "list", q: str = ""):
    clusters = repo.list_clusters()
    if not clusters:
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "clusters": [], "selected_cluster_id": 0, "page_html": ""},
        )

    if cluster_id is None:
        cluster_id = clusters[0].id

    # Полная страница
    page = _render_page(request, cluster_id=cluster_id, mode=mode, q=q)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "clusters": clusters,
            "selected_cluster_id": cluster_id,
            "mode": mode,
            "page": page,  # не используется напрямую, но удобно для отладки
        },
    )


@app.get("/page", response_class=HTMLResponse)
def page(request: Request, cluster_id: int, mode: str = "list", q: str = "", selected_news_id: int | None = None):
    # Возвращаем основной контент + OOB обновление списка кластеров (подсветка)
    resp = _render_page(request, cluster_id=cluster_id, mode=mode, q=q, selected_news_id=selected_news_id)
    return resp


@app.get("/partials/cluster_list", response_class=HTMLResponse)
def cluster_list(request: Request, selected_cluster_id: int, mode: str = "list"):
    clusters = repo.list_clusters()
    return templates.TemplateResponse(
        "partials/cluster_list.html",
        {"request": request, "clusters": clusters, "selected_cluster_id": selected_cluster_id, "mode": mode},
    )


@app.get("/clusters/{cluster_id}/news", response_class=HTMLResponse)
def news_list(request: Request, cluster_id: int, mode: str = "list", q: str = ""):
    cluster = repo.get_cluster(cluster_id)
    news = repo.search_news(cluster_id, q)
    return templates.TemplateResponse(
        "partials/news_list.html",
        {
            "request": request,
            "cluster": cluster,
            "news": news,
            "selected_cluster_id": cluster_id,
            "mode": mode,
            "q": q,
        },
    )


@app.get("/news/{news_id}/view", response_class=HTMLResponse)
def news_view(request: Request, news_id: int, cluster_id: int, mode: str = "list", q: str = ""):
    item = repo.get_news(news_id)
    # если не нашли или он не из этого кластера — показываем пусто
    if item is None or item.cluster_id != cluster_id:
        item = None
    return templates.TemplateResponse(
        "partials/news_viewer.html",
        {"request": request, "selected_news": item, "cluster_id": cluster_id, "mode": mode, "q": q},
    )


@app.post("/clusters/{cluster_id}/news/add", response_class=HTMLResponse)
def add_news(
    request: Request,
    cluster_id: int,
    mode: str = Form("list"),
    q: str = Form(""),
    title: str = Form(...),
    body: str = Form(""),
):
    repo.add_news(cluster_id, title.strip(), body.strip())
    # после добавления обновляем страницу текущего режима
    return _render_page(request, cluster_id=cluster_id, mode=mode, q=q)


@app.post("/news/{news_id}/delete", response_class=HTMLResponse)
def delete_news(
    request: Request,
    news_id: int,
    cluster_id: int = Form(...),
    mode: str = Form("list"),
    q: str = Form(""),
):
    repo.delete_news(news_id)
    return _render_page(request, cluster_id=cluster_id, mode=mode, q=q)


@app.post("/clusters/{cluster_id}/generate_draft", response_class=HTMLResponse)
def generate_draft(
    request: Request,
    cluster_id: int,
    mode: str = Form("generate"),
    q: str = Form(""),
    prompt: str = Form(""),
):
    cluster = repo.get_cluster(cluster_id)
    if cluster is None:
        return HTMLResponse("Cluster not found", status_code=404)

    title, body = gen.generate(cluster.name, prompt)
    return templates.TemplateResponse(
        "partials/generator_panel.html",
        {
            "request": request,
            "cluster_id": cluster_id,
            "mode": mode,
            "q": q,
            "prompt": prompt,
            "draft": {"title": title, "body": body},
        },
    )


@app.get("/clusters/{cluster_id}/generator_panel", response_class=HTMLResponse)
def generator_panel(request: Request, cluster_id: int, mode: str = "generate", q: str = ""):
    return templates.TemplateResponse(
        "partials/generator_panel.html",
        {
            "request": request,
            "cluster_id": cluster_id,
            "mode": mode,
            "q": q,
            "prompt": "",
            "draft": None,
        },
    )


@app.post("/clusters/{cluster_id}/news/add_generated", response_class=HTMLResponse)
def add_generated(
    request: Request,
    cluster_id: int,
    mode: str = Form("generate"),
    q: str = Form(""),
    title: str = Form(...),
    body: str = Form(""),
):
    repo.add_news(cluster_id, title.strip(), body.strip())
    # остаёмся на экране генерации, но обновляем всё содержимое
    return _render_page(request, cluster_id=cluster_id, mode=mode, q=q)
