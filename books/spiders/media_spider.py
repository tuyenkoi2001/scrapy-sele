import scrapy
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from scrapy.http import HtmlResponse
import time
import logging

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
                # Cuộn trang nhiều lần để tải hình ảnh động
                for _ in range(3):  # Cuộn 3 lần
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)  # Chờ 2 giây mỗi lần cuộn
                # Ghi log số lượng hình ảnh tìm thấy
                images = self.driver.find_elements_by_tag_name('img')
                logging.debug(f"Found {len(images)} images on {url}")
                # Lấy nội dung trang
                response = HtmlResponse(url=url, body=self.driver.page_source, encoding='utf-8')
                yield scrapy.Request(url, self.parse, dont_filter=True, meta={'response': response})
            except Exception as e:
                self.logger.error(f"Failed to load {url} with Selenium: {e}")
    
    def parse(self, response):
        # Lấy cả src và data-src (cho lazy-loaded images)
        image_urls = response.css('img::attr(src)').getall() + response.css('img::attr(data-src)').getall()
        absolute_image_urls = [urljoin(response.url, img_url) for img_url in image_urls if img_url]
        self.logger.debug(f"Extracted {len(absolute_image_urls)} image URLs: {absolute_image_urls}")
        for img_url in absolute_image_urls:
            yield {'image_url': img_url}
    
    def closed(self, reason):
        self.driver.quit()