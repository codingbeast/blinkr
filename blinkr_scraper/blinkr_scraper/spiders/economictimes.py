import re
import warnings
import scrapy
from bs4 import BeautifulSoup
from blinkr_scraper.firestore_client import summarize_to_60_words, slugify, get_2_hours_time
from transformers import pipeline
from datetime import datetime, timezone
from dateutil import parser as date_parser, tz

class EconTimesSpider(scrapy.Spider):
    name = "econ_times"
    allowed_domains = ["economictimes.indiatimes.com"]
    start_urls = ["https://economictimes.indiatimes.com/sitemap/today"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.summarizer = pipeline("summarization", model="google/flan-t5-base")

        self.exclude_keywords = ["liveblog", "videoshow"]

    def parse(self, response):
        soup = BeautifulSoup(response.text, 'xml')
        time_window, now_ist, ist = get_2_hours_time()
        urls = [
                    i.find("loc").text
                    for i in soup.find_all("url")
                    if not any(keyword in i.find("loc").text for keyword in self.exclude_keywords)
                    and i.find("news:publication_date")
                    and datetime.fromisoformat(i.find("news:publication_date").text).astimezone(ist) >= now_ist - time_window
                ]
        # Crawl the third URL as in your example; expand as needed
        for url in urls:
            category = self.get_category(url)
            allowed_categories = ["markets", "industry", "tech","wealth","small-biz","mf","ai"]
            if category in allowed_categories:
                yield scrapy.Request(url, callback=self.parse_article)
                #break
            #break
    def get_category(self, url, is_store = False):
        category_match = re.search(r".com/(.*?)/", url)
        category = category_match.group(1) if category_match else ""
        if is_store:
            if category in ["markets", "industry", "wealth", "small-biz", "mf"]:
                category = "finance"
            elif category in ['tech', "ai"]:
                category = 'technology'
        return category
    def extract_published_at(self, soup):
        meta_time = soup.find("meta", {"name": "Last-Modified"})
        if meta_time and meta_time.get("content"):
            try:
                return datetime.strptime(
                    meta_time["content"], "%A, %d %B, %Y, %I:%M:%S %p"
                ).strftime("%Y-%m-%dT%H:%M:%S")
            except Exception:
                pass
        # fallback if parsing fails or not present
        return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    def parse_article(self, response):
        soup = BeautifulSoup(response.text, 'lxml')
        title = soup.find("h1").get_text(strip=True) if soup.find("h1") else ""
        category = self.get_category(response.url, is_store=True)
        img = soup.find("meta", {"property" : "og:image"}).get("content","")
        keywords = soup.find("meta", {"name" : "keywords"}).get("content", "")
        keywords = [tag.strip().lower() for tag in keywords.split(",")] if isinstance(keywords, str) else [t.lower() for t in keywords]
        #description = soup.find("meta", {"name" : "description"}).get("content", "")
        published_at = self.extract_published_at(soup)
        article_tag = soup.find(["div", "article"], class_=["artText", "articleBody"])
        article = article_tag.get_text(separator=' ', strip=True) if article_tag else ""

        if article:
            # summary = self.summarizer(article, max_new_tokens=120, min_length=40, do_sample=False)
            summary_text = summarize_to_60_words(article, self.summarizer)
            # summary_text = summary[0]['summary_text']
        else:
            summary_text = ""

        yield {
            "title": title,
            "img" : img if img and img.startswith("http") else None,
            "tags" : keywords,
            "slug" : slugify(title),
            "category": category.strip().lower() if category else None,
            "source" : "Economic Times",
            "content": summary_text,
            "url": response.url.strip(),
            "published_at" : date_parser.parse(published_at), #published_at,
            "scraped_at" : datetime.now(timezone.utc), #datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "word_count": len(summary_text.split()) if summary_text else 0,
            "char_count": len(summary_text) if summary_text else 0,
            "author" : "blinkr",
            "language" : "en",
            "enabled" : True
        }
