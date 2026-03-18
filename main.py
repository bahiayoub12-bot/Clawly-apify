"""
Clawly-apify — Crawlee + FastAPI
بحث حر في الإنترنت بدون قيود
"""

import asyncio
import urllib.parse
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from crawlee.crawlers import BeautifulSoupCrawler, BeautifulSoupCrawlingContext

# ──────────────────────────────────────────
app = FastAPI(title="Clawly API", version="2.0.0")

# ── CORS: السماح لأي موقع بالاستدعاء ──────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────
# النماذج
# ──────────────────────────────────────────
class CrawlRequest(BaseModel):
    url: str
    max_pages: int = 5

class SearchRequest(BaseModel):
    query: str          # نص البحث الحر
    max_pages: int = 8  # عدد الصفحات المكشوطة

class PageData(BaseModel):
    url: str
    title: str | None
    content: str | None  # نص كامل بدون حد

class CrawlResponse(BaseModel):
    success: bool
    pages_crawled: int
    data: list[PageData]

class SearchResponse(BaseModel):
    success: bool
    query: str
    sources_found: int
    data: list[PageData]


# ──────────────────────────────────────────
# منطق الكشط الأساسي
# ──────────────────────────────────────────
async def run_crawler(start_url: str, max_pages: int) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    crawler = BeautifulSoupCrawler(
        max_requests_per_crawl=max_pages,
    )

    @crawler.router.default_handler
    async def handler(context: BeautifulSoupCrawlingContext) -> None:
        title = context.soup.title.string.strip() if context.soup.title else None

        # إزالة السكريبتات والستايل قبل استخراج النص
        for tag in context.soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        raw_text = context.soup.get_text(separator=" ", strip=True)
        content = " ".join(raw_text.split()) if raw_text else None

        results.append({
            "url": context.request.url,
            "title": title,
            "content": content,
        })

        await context.enqueue_links()

    await crawler.run([start_url])
    return results


# ──────────────────────────────────────────
# بحث حر: نص → محركات بحث → كشط النتائج
# ──────────────────────────────────────────
async def search_web(query: str, max_pages: int) -> list[dict[str, Any]]:
    encoded = urllib.parse.quote(query)

    # محركات بحث متعددة بدون قيود
    search_urls = [
        f"https://www.google.com/search?q={encoded}&hl=ar&num=10",
        f"https://search.yahoo.com/search?p={encoded}",
        f"https://html.duckduckgo.com/html/?q={encoded}",
        f"https://www.bing.com/search?q={encoded}",
    ]

    all_results: list[dict[str, Any]] = []

    for search_url in search_urls:
        try:
            results = await run_crawler(search_url, max_pages // len(search_urls) + 2)
            all_results.extend(results)
            if len(all_results) >= max_pages:
                break
        except Exception:
            continue

    return all_results[:max_pages]


# ──────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "ok", "message": "Clawly API is running 🚀", "version": "2.0.0"}


@app.post("/crawl", response_model=CrawlResponse)
async def crawl(request: CrawlRequest):
    """كشط URL محدد مباشرة"""
    if not request.url.startswith("http"):
        raise HTTPException(status_code=400, detail="URL يجب أن يبدأ بـ http أو https")
    try:
        data = await run_crawler(request.url, request.max_pages)
        return CrawlResponse(
            success=True,
            pages_crawled=len(data),
            data=[PageData(**item) for item in data],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """بحث حر في الإنترنت بنص عربي أو إنجليزي"""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="الرجاء إدخال نص للبحث")
    try:
        data = await search_web(request.query, request.max_pages)
        return SearchResponse(
            success=True,
            query=request.query,
            sources_found=len(data),
            data=[PageData(**item) for item in data],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
