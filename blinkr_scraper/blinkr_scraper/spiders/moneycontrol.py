import re
import warnings
import scrapy
from bs4 import BeautifulSoup
from blinkr_scraper.firestore_client import summarize_to_60_words, slugify, get_2_hours_time
from transformers import pipeline
from datetime import datetime

class moneyControlSpider(scrapy.Spider):
    name = "moneycontrol"
    allowed_domains = ["www.moneycontrol.com"]
    start_urls = ["https://www.moneycontrol.com/news/news-sitemap.xml"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.summarizer = pipeline("summarization", model="google/flan-t5-base")
        self.allowed_categories = ["business", "technology"]
        self.exclude_keywords = ["personal-finance"]

    def parse(self, response):
        soup = BeautifulSoup(response.text, 'xml')
        time_window, now_ist, ist = get_2_hours_time()
        urls = [
                    i.find("loc").text
                    for i in soup.find_all("url")
                    if not any(keyword in i.find("loc").text for keyword in self.exclude_keywords)
                    and i.find("lastmodlastmod")
                    and datetime.fromisoformat(i.find("lastmodlastmod").text).astimezone(ist) >= now_ist - time_window
                ]
        # Crawl the third URL as in your example; expand as needed
        for url in urls:
            category = self.get_category(url, self.allowed_categories)
            if category in self.allowed_categories:
                yield scrapy.Request(url, callback=self.parse_article)
                #break
            #break
    def get_category(self, url,allowed_categories : None, is_store = False):
        category = next(
            (cat for cat in allowed_categories if re.search(rf"/{cat}/", url)), 
            ""
        )
        if is_store:
            if category in ["business"]:
                category = "finance"
            elif category in ["technology"]:
                category = 'technology'
        return category
    def extract_published_at(self, soup):
        meta_time = soup.find("meta", {"name": "Last-Modified"})
        if meta_time and meta_time.get("content"):
            try:
                # parse ISO 8601 with timezone
                return datetime.fromisoformat(meta_time["content"]).strftime("%Y-%m-%dT%H:%M:%S")
            except Exception:
                pass
        # fallback if parsing fails or not present
        return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    def parse_article(self, response):
        soup = BeautifulSoup(response.text, 'lxml')
        title = soup.find("h1",{"class" : "article_title artTitle"}).get_text(strip=True) if soup.find("h1",{"class" : "article_title artTitle"}) else ""
        category = self.get_category(response.url,self.allowed_categories, is_store=True)
        img = soup.find("meta", {"property" : "og:image"}).get("content","")
        keywords = soup.find("meta", {"name" : "news_keywords"}).get("content", "")
        #description = soup.find("meta", {"name" : "description"}).get("content", "")
        published_at = self.extract_published_at(soup)
        article_tag = soup.find("div", {"id" : "contentdata"})
        article = article_tag.get_text(separator=' ', strip=True) if article_tag else ""
        
        if article:
            # summary = self.summarizer(article, max_new_tokens=120, min_length=40, do_sample=False)
            summary_text = summarize_to_60_words(article, self.summarizer)
            # summary_text = summary[0]['summary_text']
        else:
            summary_text = ""
        
        yield {
            "title": title,
            "img" : img,
            "tags" : keywords,
            "slug" : slugify(title),
            "category": category,
            "source" : "moneycontrol",
            "content": summary_text,
            "url": response.url,
            "published_at" : published_at,
            "scraped_at" : datetime.datetime.utcnow(), #datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "author" : "blinkr",
            "language" : "en",
            "enabled" : True
        }