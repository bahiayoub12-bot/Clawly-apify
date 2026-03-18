"""
Clawly-apify — Crawlee + FastAPI
متصفح حقيقي (Playwright) — يدخل أي موقع بدون قيود
"""

import asyncio
import urllib.parse
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext

# ──────────────────────────────────────────
app = FastAPI(title="Clawly API", version="3.0.0")

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
    query: str
    max_pages: int = 8

class PageData(BaseModel):
    url: str
    title: str | None
    content: str | None

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
# الكشط بـ Playwright (متصفح حقيقي)
# ──────────────────────────────────────────
async def run_crawler(start_url: str, max_pages: int) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    crawler = PlaywrightCrawler(
        max_requests_per_crawl=max_pages,
        headless=True,
        browser_type="chromium",
    )

    @crawler.router.default_handler
    async def handler(context: PlaywrightCrawlingContext) -> None:
        # انتظر تحميل الصفحة كاملاً
        await context.page.wait_for_load_state("networkidle")

        title = await context.page.title()

        # استخراج النص الكامل بعد تشغيل JavaScript
        content = await context.page.evaluate("""() => {
            // إزالة العناصر غير المفيدة
            ['script','style','nav','footer','header','aside','ads'].forEach(tag => {
                document.querySelectorAll(tag).forEach(el => el.remove())
            });
            return document.body.innerText;
        }""")

        content = " ".join(content.split()) if content else None

        results.append({
            "url": context.request.url,
            "title": title or None,
            "content": content,
        })

        await context.enqueue_links()

    await crawler.run([start_url])
    return results


# ──────────────────────────────────────────
# بحث حر في محركات متعددة
# ──────────────────────────────────────────
async def search_web(query: str, max_pages: int) -> list[dict[str, Any]]:
    encoded = urllib.parse.quote(query)

    # محركات بحث + مواقع أخبار مباشرة
    search_urls = [
        f"https://www.bing.com/search?q={encoded}",
        f"https://html.duckduckgo.com/html/?q={encoded}",
        f"https://www.google.com/search?q={encoded}&hl=ar&num=10",
        f"https://search.yahoo.com/search?p={encoded}",
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
    return {"status": "ok", "message": "Clawly API is running 🚀", "version": "3.0.0"}


@app.post("/crawl", response_model=CrawlResponse)
async def crawl(request: CrawlRequest):
    """كشط أي URL مباشرة بمتصفح حقيقي"""
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
    """بحث حر في الإنترنت — يدخل أي موقع"""
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
