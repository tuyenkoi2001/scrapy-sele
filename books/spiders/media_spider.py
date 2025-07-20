import scrapy
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from scrapy.http import HtmlResponse
import time

class MediaSpider(scrapy.Spider):
    name = 'media_spider'
    
    def __init__(self, start_url=None, result=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = [start_url] if start_url else []
        self.result = result
    
    def start_requests(self):
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        for url in self.start_urls:
            try:
                self.driver.get(url)
                # Cuộn trang để tải hình ảnh động
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)  # Chờ tải hình ảnh
                # Lấy nội dung trang
                response = HtmlResponse(url=url, body=self.driver.page_source, encoding='utf-8')
                yield scrapy.Request(url, self.parse, dont_filter=True, meta={'response': response})
            except Exception as e:
                self.logger.error(f"Failed to load {url} with Selenium: {e}")
    
    def parse(self, response):
        # Lấy tất cả src từ thẻ img
        image_urls = response.css('img::attr(src)').getall()
        absolute_image_urls = [urljoin(response.url, img_url) for img_url in image_urls if img_url]
        for img_url in absolute_image_urls:
            yield {'image_url': img_url}
    
    def closed(self, reason):
        self.driver.quit()