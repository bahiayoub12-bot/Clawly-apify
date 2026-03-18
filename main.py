import os
import urllib.parse
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from crawlee.playwright_crawler import PlaywrightCrawler, PlaywrightCrawlingContext

app = FastAPI(title="Albert Ultimate Crawler", version="2.0.0")

# 1. حل مشكلة الحظر في المتصفح (CORS) - ضروري جداً
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. تعريف البيانات الصادرة
class PageData(BaseModel):
    url: str
    content: str

# 3. محرك البحث الذكي (باستخدام Playwright لدعم كل المواقع)
async def run_smart_crawler(target_url: str):
    results = []
    # نستخدم Playwright لأنه يفتح المواقع كأنه إنسان (يدعم JS)
    crawler = PlaywrightCrawler(max_requests_per_crawling=1)

    @crawler.router.default_handler
    async def handler(context: PlaywrightCrawlingContext):
        # تسريع العملية بحظر الصور والإعلانات
        await context.page.route("**/*.{png,jpg,jpeg,gif,svg,css,pdf}", lambda route: route.abort())
        
        # استخراج النص النظيف
        text = await context.page.locator('body').inner_text()
        results.append({"url": context.request.url, "content": text[:4000]})

    await crawler.run([target_url])
    return results

# 4. النقطة الشاملة (تستقبل GET و POST وتدعم كل المسميات)
@app.api_route("/search", methods=["GET", "POST"])
@app.api_route("/crawl", methods=["GET", "POST"])
@app.api_route("/scrape", methods=["GET", "POST"])
async def universal_api(request: Request, url: str = Query(None)):
    # جلب الرابط وفك تشفيره نهائياً
    target_url = url
    if request.method == "POST":
        try:
            body = await request.json()
            target_url = body.get("url", url)
        except: pass

    if not target_url:
        raise HTTPException(status_code=400, detail="الرابط مطلوب")

    # فك التشفير (العلاج الجذري)
    decoded_url = urllib.parse.unquote(target_url)

    try:
        data = await run_smart_crawler(decoded_url)
        return {"success": True, "data": data[0]["content"] if data else "لا يوجد محتوى"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/")
def health():
    return {"status": "online", "boss": "Albert Samara"}
