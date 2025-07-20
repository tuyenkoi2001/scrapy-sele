from fastapi import FastAPI, HTTPException
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from books.spiders.media_spider import MediaSpider
import crochet
import logging
from typing import List
from pydantic import HttpUrl

crochet.setup()
app = FastAPI()
logging.basicConfig(level=logging.DEBUG)

class ScrapeResult:
    def __init__(self):
        self.image_urls = []

    def add_image(self, url: str):
        self.image_urls.append(url)

@app.get("/")
@app.head("/")
async def root():
    return {"status": "API is running"}

@crochet.run_in_reactor
def run_spider(start_url: str) -> ScrapeResult:
    result = ScrapeResult()
    logging.debug(f"Starting spider for URL: {start_url}")
    try:
        settings = get_project_settings()
        settings.set('ITEM_PIPELINES', {'__main__.ResultPipeline': 100}, priority='cmdline')
        settings.set('DOWNLOAD_TIMEOUT', 600)
        process = CrawlerProcess(settings)
        crawler = process.create_crawler(MediaSpider)
        process.crawl(crawler, start_url=start_url, result=result)
        process.start()
        return result
    except Exception as e:
        logging.error(f"Spider failed: {e}")
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

class ResultPipeline:
    def process_item(self, item, spider):
        spider.crawler.settings.get('result').add_image(item['image_url'])
        return item

@app.post("/scrape")
async def scrape(url: HttpUrl):
    if not str(url).startswith(('http://', 'https://')):
        raise HTTPException(status_code=400, detail="Invalid URL. Must start with http:// or https://")

    result = run_spider(str(url))
    result.wait(timeout=600)
    if not result.result.image_urls:
        raise HTTPException(status_code=404, detail="No images found on the provided URL")
    
    return {"image_urls": result.result.image_urls}

@app.get("/scrape")
async def scrape_get(url: HttpUrl):
    return await scrape(url)