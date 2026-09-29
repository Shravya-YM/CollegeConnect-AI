import os
import sys
from pathlib import Path

# Add backend to sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.services.crawler import VVCEWebCrawler
from app.core.config import settings

def main():
    print(f"==================================================")
    print(f" Starting VVCE Web Crawler for CollegeConnect AI ")
    print(f" Target Root: {settings.COLLEGE_BASE_URL} ")
    print(f"==================================================")

    crawler = VVCEWebCrawler()
    pages = crawler.crawl_urls(max_pages=15)

    print(f"\n[+] Successfully crawled {len(pages)} pages from VVCE official portal.")
    print(f"[+] Raw data saved to: {settings.RAW_DATA_DIR}/crawled_vvce_pages.json")

if __name__ == "__main__":
    main()
