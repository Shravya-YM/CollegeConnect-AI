import os
import json
import time
import logging
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
from app.core.config import settings
from app.core.sanitizer import sanitize_scraped_text

logger = logging.getLogger(__name__)

# Core high-priority seed URLs from https://vvce.ac.in
DEFAULT_VVCE_SEED_URLS = [
    "https://vvce.ac.in/",
    "https://vvce.ac.in/about/",
    "https://vvce.ac.in/admissions/",
    "https://vvce.ac.in/cut-off-ranks/",
    "https://vvce.ac.in/autonomous-regulations/",
    "https://vvce.ac.in/autonomous-scheme-syllabus/",
    "https://vvce.ac.in/departments/department-of-computer-science-and-engineering/",
    "https://vvce.ac.in/departments/department-of-information-science-and-engineering/",
    "https://vvce.ac.in/departments/department-of-artificial-intelligence-and-machine-learning/",
    "https://vvce.ac.in/departments/department-of-electronics-and-communication-engineering/",
    "https://vvce.ac.in/departments/department-of-electrical-and-electronics-engineering/",
    "https://vvce.ac.in/departments/department-of-mechanical-engineering/",
    "https://vvce.ac.in/departments/department-of-civil-engineering/",
    "https://vvce.ac.in/departments/department-of-business-administration/",
    "https://vvce.ac.in/contact-us/",
    "https://vvce.ac.in/careers/",
]

class VVCEWebCrawler:
    def __init__(self, headers: dict = None):
        self.headers = headers or {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 CollegeConnectBot/1.0"
        }

    def fetch_page(self, url: str, timeout: int = 15) -> str:
        """Fetches raw HTML from a given URL."""
        req = urllib.request.Request(url, headers=self.headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="ignore")

    def extract_page_data(self, url: str, html: str) -> dict:
        """Parses HTML into cleaned, structured text and metadata."""
        soup = BeautifulSoup(html, "html.parser")

        # 1. Extract Title
        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        elif soup.find("h1"):
            title = soup.find("h1").get_text(strip=True)
        else:
            title = url

        # Clean title suffix (e.g. " - Vidyavardhaka College of Engineering")
        title = re_clean_title = title.split(" - ")[0].split(" | ")[0].strip()

        # 2. Decompose unneeded UI elements
        for element in soup(["script", "style", "nav", "footer", "aside", "noscript", "svg", "form"]):
            element.decompose()

        # 3. Locate main content container if possible (Elementor or standard article)
        content_container = (
            soup.find("div", class_="elementor-widget-wrap")
            or soup.find("article")
            or soup.find("main")
            or soup.find("div", class_="entry-content")
            or soup.body
            or soup
        )

        # 4. Extract text while preserving header structure & tables
        lines = []
        for tag in content_container.find_all(["h1", "h2", "h3", "h4", "p", "li", "table"]):
            if tag.name in ["h1", "h2", "h3", "h4"]:
                heading_level = "#" * int(tag.name[1])
                heading_text = tag.get_text(strip=True)
                if heading_text:
                    lines.append(f"\n{heading_level} {heading_text}\n")
            elif tag.name == "p":
                p_text = tag.get_text(strip=True)
                if p_text:
                    lines.append(p_text)
            elif tag.name == "li":
                li_text = tag.get_text(strip=True)
                if li_text:
                    lines.append(f"- {li_text}")
            elif tag.name == "table":
                # Convert table to readable markdown/text
                table_rows = []
                for row in tag.find_all("tr"):
                    cells = [cell.get_text(strip=True) for cell in row.find_all(["th", "td"])]
                    if any(cells):
                        table_rows.append(" | ".join(cells))
                if table_rows:
                    lines.append("\n" + "\n".join(table_rows) + "\n")

        raw_text = "\n\n".join(lines)
        sanitized_text, injection_detected = sanitize_scraped_text(raw_text)

        return {
            "url": url,
            "title": title,
            "text": sanitized_text,
            "injection_detected": injection_detected,
            "crawled_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

    def crawl_urls(self, urls: list[str] = None, max_pages: int = 20) -> list[dict]:
        """Crawls a list of seed URLs with rate limiting and saves to raw data dir."""
        urls_to_crawl = urls or DEFAULT_VVCE_SEED_URLS
        scraped_documents = []

        for i, url in enumerate(urls_to_crawl[:max_pages]):
            try:
                logger.info(f"Crawling ({i+1}/{len(urls_to_crawl)}): {url}")
                html = self.fetch_page(url)
                doc = self.extract_page_data(url, html)
                if len(doc["text"]) > 100:  # Skip empty/stub pages
                    scraped_documents.append(doc)
                time.sleep(1.0)  # Politeness delay
            except Exception as e:
                logger.warning(f"Failed to crawl {url}: {e}")

        # Save scraped raw docs
        output_file = os.path.join(settings.RAW_DATA_DIR, "crawled_vvce_pages.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(scraped_documents, f, indent=2, ensure_ascii=False)

        return scraped_documents
