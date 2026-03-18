import os
import urllib.parse
from fastapi import FastAPI, Query, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from crawlee.playwright_crawler import PlaywrightCrawler, PlaywrightCrawlingContext

app = FastAPI()

# حل مشكلة الحظر من المتصفح (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ميكانيكية الكشط
async def run_the_crawl(target_url: str):
    results = []
    # ملاحظة: نستخدم playwright_crawler لضمان تشغيل المواقع التي تعتمد على JS
    crawler = PlaywrightCrawler(max_requests_per_crawling=1)

    @crawler.router.default_handler
    async def handler(context: PlaywrightCrawlingContext):
        # تعطيل الصور لتسريع العملية
        await context.page.route("**/*.{png,jpg,jpeg,gif,svg,css}", lambda route: route.abort())
        content = await context.page.locator('body').inner_text()
        results.append(content[:4000])

    await crawler.run([target_url])
    return results[0] if results else "No content found"

# 🚪 هذا هو "المستقبل الشامل" لجميع طلباتك
@app.api_route("/{path:path}", methods=["GET", "POST"])
async def catch_all(request: Request, path: str, url: str = Query(None)):
    # جلب الرابط سواء من Query string أو من Body
    target_url = url
    if request.method == "POST":
        try:
            body = await request.json()
            target_url = body.get("url", url)
        except: pass

    if not target_url:
        return {"status": "error", "message": "Missing URL"}

    # فك تشفير الرابط نهائياً
    decoded_url = urllib.parse.unquote(target_url)

    # التحقق من أن المسار المطلوب هو أحد المسارات التي نستخدمها
    valid_paths = ["search", "crawl", "scrape", "fetch"]
    if path not in valid_paths:
        return {"status": "ok", "message": f"Path {path} is active, but send a valid request."}

    try:
        data = await run_the_crawl(decoded_url)
        return {"status": "success", "data": data, "url": decoded_url}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/")
def home():
    return {"status": "active", "owner": "Albert Samara"}
