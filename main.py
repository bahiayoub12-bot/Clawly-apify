"""
my-crawler — Crawlee + FastAPI
يستقبل URL ويعيد البيانات المكشوطة عبر API
"""

import asyncio
import os
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from crawlee.crawlers import BeautifulSoupCrawler, BeautifulSoupCrawlingContext

# ──────────────────────────────────────────
app = FastAPI(title="My Crawler API", version="1.0.0")


# ── نماذج الطلب والرد ──────────────────────
class CrawlRequest(BaseModel):
    url: str
    max_pages: int = 5  # عدد الصفحات الأقصى


class PageData(BaseModel):
    url: str
    title: str | None
    text_preview: str | None  # أول 500 حرف من النص


class CrawlResponse(BaseModel):
    success: bool
    pages_crawled: int
    data: list[PageData]


# ── منطق الكشط ────────────────────────────
async def run_crawler(start_url: str, max_pages: int) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    crawler = BeautifulSoupCrawler(
        max_requests_per_crawl=max_pages,
    )

    @crawler.router.default_handler
    async def handler(context: BeautifulSoupCrawlingContext) -> None:
        # استخراج العنوان
        title = context.soup.title.string.strip() if context.soup.title else None

        # استخراج النص الخام وتنظيفه
        raw_text = context.soup.get_text(separator=" ", strip=True)
        text_preview = raw_text[:500] if raw_text else None

        results.append({
            "url": context.request.url,
            "title": title,
            "text_preview": text_preview,
        })

        # متابعة الروابط داخل نفس الدومين
        await context.enqueue_links()

    await crawler.run([start_url])
    return results


# ── نقاط الوصول (Endpoints) ───────────────
@app.get("/")
def root():
    return {"status": "ok", "message": "Crawler API is running 🚀"}


@app.post("/crawl", response_model=CrawlResponse)
async def crawl(request: CrawlRequest):
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


# ── تشغيل مباشر (اختياري) ─────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
