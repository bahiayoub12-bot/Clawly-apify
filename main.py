import os
import urllib.parse
from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from crawlee.playwright_crawler import PlaywrightCrawler, PlaywrightCrawlingContext

app = FastAPI()

# حل مشكلة الحظر من المتصفح (CORS) ليعمل تطبيقك بسلاسة
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# محرك الكشط باستخدام Playwright (الأقوى للمواقع الحديثة)
async def run_crawler(target_url: str):
    results = []
    crawler = PlaywrightCrawler(max_requests_per_crawling=1)
    @crawler.router.default_handler
    async def handler(context: PlaywrightCrawlingContext):
        # منع تحميل الصور لتسريع العملية وتوفير الموارد
        await context.page.route("**/*.{png,jpg,jpeg,gif,svg,css}", lambda route: route.abort())
        content = await context.page.locator('body').inner_text()
        results.append(content[:4000])
    await crawler.run([target_url])
    return results[0] if results else "No content"

# استقبال أي مسار (search, crawl, scrape) وأي طريقة (GET, POST)
@app.api_route("/{path:path}", methods=["GET", "POST"])
async def catch_all(request: Request, path: str, url: str = Query(None)):
    target_url = url
    if request.method == "POST":
        try:
            body = await request.json()
            target_url = body.get("url", url)
        except: pass

    if not target_url:
        return {"success": False, "error": "Missing URL"}

    # العلاج النهائي لروابط جوجل الطويلة (Unquote)
    decoded_url = urllib.parse.unquote(target_url)

    try:
        data = await run_crawler(decoded_url)
        return {"success": True, "data": data, "url": decoded_url}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/")
def health(): return {"status": "Active", "owner": "Albert Samara"}
