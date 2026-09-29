import pytest
from app.services.crawler import VVCEWebCrawler
from app.services.processor import chunk_text, DocumentProcessor

SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head><title>Cut-Off Ranks - Vidyavardhaka College of Engineering</title></head>
<body>
  <nav><a href="/">Home</a></nav>
  <main>
    <h1>KCET and COMEDK Cut-Off Ranks</h1>
    <p>VVCE offers B.E. admissions based on KCET and COMEDK entrance ranks.</p>
    <table>
      <tr><th>Course</th><th>KCET Cut-off</th></tr>
      <tr><td>Computer Science and Engineering</td><td>12500</td></tr>
      <tr><td>Artificial Intelligence & Machine Learning</td><td>16800</td></tr>
    </table>
  </main>
  <footer><p>© 2026 VVCE</p></footer>
</body>
</html>
"""

def test_crawler_page_extraction():
    crawler = VVCEWebCrawler()
    url = "https://vvce.ac.in/cut-off-ranks/"
    data = crawler.extract_page_data(url, SAMPLE_HTML)

    assert data["title"] == "Cut-Off Ranks"
    assert "Computer Science and Engineering | 12500" in data["text"]
    assert "© 2026 VVCE" not in data["text"]  # Footer stripped
    assert "Home" not in data["text"]  # Nav stripped

def test_chunking_and_metadata_enrichment():
    processor = DocumentProcessor(chunk_size=150, overlap=30)
    docs = [{
        "url": "https://vvce.ac.in/cut-off-ranks/",
        "title": "Cut-Off Ranks",
        "text": "This is a detailed paragraph explaining B.Tech admissions at VVCE. It covers entrance exams such as KCET, COMEDK, and management quota criteria for prospective students."
    }]

    chunks = processor.process_documents(docs)
    assert len(chunks) >= 1
    primary = chunks[0]
    assert "Context: [VVCE Official Website > Cut-Off Ranks]" in primary["text"]
    assert "Source URL: https://vvce.ac.in/cut-off-ranks/" in primary["text"]
    assert primary["url"] == "https://vvce.ac.in/cut-off-ranks/"
