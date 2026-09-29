# CollegeConnect AI: RAG Chatbot for Vidyavardhaka College of Engineering (VVCE)

**CollegeConnect AI** is an enterprise-grade Retrieval-Augmented Generation (RAG) conversational agent engineered for **Vidyavardhaka College of Engineering (VVCE, Mysuru)**. It ingests verified data from the official college portal (`https://vvce.ac.in`), stores contextual chunk embeddings in **ChromaDB**, applies **Hybrid Search (Dense + BM25 with Reciprocal Rank Fusion)**, enforces **Measurable Grounding & Evidence Sufficiency Gating**, and streams grounded answers with verified source citations to an **embeddable JavaScript web widget**.

---

## 🌟 Key Features

1. **Official VVCE Knowledge Extraction**: Crawls and structures pages from `https://vvce.ac.in/` (Admissions, Cut-offs, Autonomous Syllabi, Departments, Placements, and Administration).
2. **Measurable Grounding & Evidence Sufficiency Gating**:
   - Rejects ungrounded speculation: if the retrieved similarity is below threshold ($\tau = 0.65$) or evidence is absent, the chatbot issues the designated official refusal disclaimer.
   - Evaluated against quantitative faithfulness metrics ($\ge 95\%$ factual claim entailment) and $100\%$ refusal specificity on out-of-scope questions.
3. **Indirect Prompt Injection Defense**:
   - Strips malicious control tokens, hidden styles, and role-override payloads from crawled web content.
   - Isolates context in structured `<vvce_context>` XML blocks instructing the model to treat retrieved data strictly as passive reference text.
4. **Security & Production Hardening**:
   - **Rate Limiting**: `slowapi` restricts request rates (default `20/minute` per IP).
   - **Admin API Protection**: Ingestion and indexing endpoints require a timing-safe `X-Admin-API-Key` header.
5. **Drop-in Embeddable Web Widget**:
   - Zero external frontend dependencies.
   - VVCE branding: `#1B365D` (navy) with gold accents.
   - Server-Sent Events (SSE) token streaming.
   - Interactive source citation pills linking directly to original VVCE web pages.

---

## 📁 Repository Structure

```text
CollegeConnect-AI/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── chat.py             # POST /api/chat & SSE /api/chat/stream
│   │   │   ├── ingest.py           # Admin-protected POST /api/ingest/trigger
│   │   │   ├── health.py           # GET /api/health
│   │   │   └── evaluation.py       # POST /api/eval/run
│   │   ├── core/
│   │   │   ├── config.py           # Settings, paths, thresholds
│   │   │   ├── security.py         # Timing-safe API key validation
│   │   │   └── sanitizer.py        # Indirect prompt injection cleaner
│   │   ├── services/
│   │   │   ├── crawler.py          # VVCE web crawler & HTML parser
│   │   │   ├── processor.py        # Hierarchical chunker & breadcrumb tagger
│   │   │   ├── vector_store.py     # ChromaDB wrapper with Gemini/fallback embeddings
│   │   │   ├── hybrid_search.py    # BM25 + Dense Reciprocal Rank Fusion (RRF)
│   │   │   └── rag_service.py      # Grounded generation & SSE token streamer
│   │   └── main.py                 # FastAPI application with CORS & rate limiting
│   ├── data/
│   │   ├── raw/                    # Cached scraped raw pages (JSON)
│   │   ├── processed/              # Cleaned contextual chunks
│   │   └── chromadb/               # Persistent vector store database
│   ├── tests/
│   │   ├── benchmark_data.json     # 26 golden benchmark queries & negative probes
│   │   ├── test_security.py        # Rate limiting, auth, injection tests
│   │   ├── test_crawler.py         # Crawler and parser tests
│   │   ├── test_retrieval.py       # BM25, RRF, evidence gating tests
│   │   ├── test_faithfulness.py    # Grounding & refusal tests
│   │   └── test_api.py             # FastAPI endpoint tests
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── widget/
│   │   ├── widget.js               # Zero-dependency embeddable JavaScript widget
│   │   ├── widget.css              # Branded VVCE styles
│   │   └── test_college_page.html  # Mock VVCE portal demonstrating live widget
│   └── package.json
├── scripts/
│   ├── run_crawler.py              # CLI crawler runner
│   ├── run_ingest.py               # Full indexing & vector pipeline runner
│   └── run_evaluation.py           # Golden benchmark evaluation runner
└── README.md
```

---

## 🚀 Quickstart Guide

### 1. Configure Environment
Copy `.env.example` to `.env` in the `backend/` directory:
```powershell
cd C:\Users\splif\CollegeConnect-AI\backend
Copy-Item .env.example .env
```
Open `.env` and configure your settings:
```ini
GEMINI_API_KEY=your_gemini_api_key_here
ADMIN_API_KEY=vvce_admin_secret_key_change_me
RATE_LIMIT_PER_MINUTE=20/minute
EVIDENCE_THRESHOLD=0.65
```
*(Note: If `GEMINI_API_KEY` is omitted, the system operates in offline extractive grounding mode).*

---

### 2. Crawl & Ingest VVCE Data
Run the end-to-end ingestion pipeline to fetch live data from `https://vvce.ac.in`, chunk it, embed it into ChromaDB, and build the BM25 index:
```powershell
python scripts/run_ingest.py
```

---

### 3. Launch the Backend API
Start the FastAPI server:
```powershell
cd backend
uvicorn app.main:app --reload --port 8000
```
- Interactive API Docs: `http://localhost:8000/docs`
- Health Endpoint: `http://localhost:8000/api/health`

---

### 4. Test the Embeddable Chat Widget
Open `frontend/widget/test_college_page.html` in your browser.
1. Click the floating circular chat bubble in the bottom-right corner.
2. Click any of the quick-action chips (e.g., *"What are the cutoff ranks?"*, *"Tell me about CSE"*).
3. Observe real-time token streaming and clickable source citations pointing to `https://vvce.ac.in`.

---

## 🔬 Evaluation & Testing Suite

Run the automated test suites:
```powershell
# Run security & injection protection tests
pytest backend/tests/test_security.py -v

# Run crawler & chunking tests
pytest backend/tests/test_crawler.py -v

# Run retrieval accuracy & evidence sufficiency tests
pytest backend/tests/test_retrieval.py -v

# Run faithfulness & refusal tests
pytest backend/tests/test_faithfulness.py -v

# Run all automated tests
pytest backend/tests/ -v
```

### Run Golden Benchmark Scorecard
Execute the 26-query benchmark evaluation measuring Hit@K, MRR@5, Faithfulness, Refusal Specificity, and Citation Precision:
```powershell
python scripts/run_evaluation.py
```

---

## 🌐 Official College Website Integration

To deploy CollegeConnect AI onto the official VVCE college website, the webmaster simply adds the following single line before the closing `</body>` tag on any page:

```html
<script
  src="https://chat.vvce.ac.in/widget.js"
  data-api-url="https://api-chat.vvce.ac.in"
  data-college-name="VVCE"
  defer>
</script>
```

### Production Security Checklist:
- **CORS Configuration**: In `backend/.env`, set `ALLOWED_ORIGINS=https://www.vvce.ac.in,https://vvce.ac.in`.
- **Content Security Policy (CSP)**: Ensure the college site permits the widget connection:
  `Content-Security-Policy: connect-src 'self' https://api-chat.vvce.ac.in; script-src 'self' https://chat.vvce.ac.in;`
