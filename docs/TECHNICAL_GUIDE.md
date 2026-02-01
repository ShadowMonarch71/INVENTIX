# Inventix AI - Technical Documentation
## For Team Members

---

## 🏗️ Project Architecture

### Overview
Inventix AI is a full-stack web application with:
- **Frontend**: Next.js 14 (React) with TypeScript
- **Backend**: FastAPI (Python) with async support
- **AI Engine**: Google Gemini API for SLM (Small Language Model) tasks
- **Database**: SQLite (for MVP)

```
INVENTIX/
├── frontend/               # Next.js React application
│   ├── src/
│   │   ├── app/           # Next.js app router
│   │   ├── components/    # React components
│   │   │   ├── panels/    # Main panel components
│   │   │   └── ui/        # Reusable UI components
│   │   └── context/       # React context providers
│   └── public/            # Static assets
│
├── backend/               # FastAPI Python backend
│   ├── app/
│   │   ├── api/          # API routes
│   │   │   └── routes/   # Individual route files
│   │   ├── services/     # Business logic services
│   │   ├── core/         # Core schemas and models
│   │   └── config.py     # Configuration management
│   └── requirements.txt  # Python dependencies
│
└── docs/                 # Documentation
```

---

## 🔧 How to Run Locally

### Prerequisites
- Node.js 18+
- Python 3.10+
- Git

### Setup Steps

```bash
# 1. Clone the repository
git clone https://github.com/ShadowMonarch71/INVENTIX.git
cd INVENTIX

# 2. Setup Backend
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# 3. Create .env file in root directory
# Add: GEMINI_API_KEY=your_api_key_here

# 4. Start Backend
python -m uvicorn app.main:app --reload --port 8000

# 5. In another terminal, setup Frontend
cd frontend
npm install
npm run dev

# 6. Open http://localhost:3000
```

---

## 🧠 Core ANTIGRAVITY Features (Technical Deep Dive)

### 1. Document Processing (`document_processor.py`)

**Purpose**: Extract text from PDF, DOCX, and TXT files

**How it works**:
```python
# Uses pypdf for PDFs, python-docx for Word docs
class DocumentProcessor:
    def process_document(content, filename, content_type):
        # 1. Detect file type from extension/content-type
        # 2. Extract raw text using appropriate library
        # 3. Normalize text (clean whitespace, fix encoding)
        # 4. Split into sections/paragraphs
        # 5. Return structured DocumentResult
```

**Key Output**:
- `text`: Extracted text content
- `word_count`: Total words
- `paragraph_count`: Number of paragraphs
- `sections`: Detected document sections

---

### 2. Concept Extraction (`concept_extractor.py`)

**Purpose**: Extract keywords and distinguish novel vs common terms

**How it works**:
```python
class ConceptExtractor:
    async def extract_concepts(text, use_slm=True):
        # Step 1: Deterministic extraction (regex patterns)
        # - Find capitalized phrases
        # - Extract technical terms (acronyms, hyphenated words)
        
        # Step 2: SLM-assisted categorization
        # - Send to Gemini with prompt asking to categorize
        # - Categories: differentiating, methodological, common_domain
        
        # Step 3: Term weighting
        # - Weight by frequency and position
        # - Higher weight for terms in title/abstract
```

**Output Categories**:
- `differentiating_terms`: Potentially novel concepts (highlight these!)
- `common_terms`: Standard domain vocabulary
- `methodological`: Research/patent methodology terms

---

### 3. Prior Art Comparison (`prior_art_comparator.py`)

**Purpose**: Compare user's idea against existing work, assess novelty risk

**How it works**:
```python
class PriorArtComparator:
    async def compare_with_prior_art(user_text, user_title, project_type):
        # 1. Build comparison prompt with user's content
        # 2. Ask Gemini to generate realistic prior art matches
        # 3. For each match, calculate:
        #    - similarity_score (0-1)
        #    - overlapping_concepts
        #    - differentiating_aspects
        
        # 4. Calculate overall risk:
        #    - GREEN (0-0.3): Low overlap, safe to proceed
        #    - YELLOW (0.3-0.6): Moderate overlap, needs differentiation
        #    - RED (0.6-1.0): High overlap, significant prior art exists
```

**Risk Classification**:
| Risk | Score Range | Meaning |
|------|-------------|---------|
| 🟢 GREEN | 0.0 - 0.3 | Low overlap, likely novel |
| 🟡 YELLOW | 0.3 - 0.6 | Partial overlap, needs work |
| 🔴 RED | 0.6 - 1.0 | High overlap, crowded space |

---

### 4. Research Summarizer (`research_summarizer.py`)

**Purpose**: Generate structured, evidence-grounded summaries

**How it works**:
```python
class ResearchSummarizer:
    async def generate_summary(user_text, user_title, project_type):
        # Generates 4 distinct sections:
        # 1. existing_work: What already exists in the field
        # 2. user_contribution: What THIS project adds
        # 3. differentiation: HOW it differs from prior art
        # 4. uncertainty: Areas with insufficient evidence
        
        # Also extracts:
        # - key_innovations: List of novel aspects
        # - confidence_level: low/medium/high
```

**Critical Rules**:
- ❌ Never fabricate claims
- ❌ Never invent data or citations
- ✅ Only summarize what's in the provided text
- ✅ Use hedging language ("appears to", "suggests", "may")

---

### 5. Draft Refiner (`draft_refiner.py`)

**Purpose**: Improve writing quality without adding claims

**How it works**:
```python
class DraftRefiner:
    async def refine_draft(original_text, focus_areas, max_change_level):
        # Refinement types:
        # - CLARITY: Simplify complex sentences
        # - STRUCTURE: Improve paragraph flow
        # - PRECISION: Replace vague terms with specific ones
        # - GRAMMAR: Fix grammatical errors
        # - CONCISENESS: Remove redundant phrases
        
        # Critical: CLAIM PRESERVATION
        # - Extract all claims from original
        # - Verify all claims exist in refined version
        # - Flag if any claims are missing
```

**Output**:
- `refined_text`: Improved version
- `changes`: List of specific changes made
- `preserved_claims`: Verification that claims weren't altered
- `warnings`: AI artifact detection

---

### 6. SLM Engine (`slm_engine.py`)

**Purpose**: Wrapper around Gemini API with safety features

**Key Features**:
```python
class SLMEngine:
    def __init__(self):
        # Uses gemini-1.5-flash model
        # Low temperature (0.3) for deterministic outputs
        
    async def generate(request: SLMRequest):
        # 1. Build prompt with system instructions
        # 2. Call Gemini API
        # 3. Parse JSON response
        # 4. Handle rate limiting (429) with retry logic
        # 5. Return structured SLMResponse
```

**Rate Limiting**:
- Retries up to 3 times on 429 errors
- Exponential backoff: 2s, 4s, 8s delays

---

## 🌐 API Endpoints

### Base URL: `http://localhost:8000`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/antigravity/document/upload` | POST | Upload PDF/DOCX/TXT |
| `/api/antigravity/concepts/extract` | POST | Extract concepts |
| `/api/antigravity/prior-art/compare` | POST | Compare with prior art |
| `/api/antigravity/summary/generate` | POST | Generate summary |
| `/api/antigravity/refine/draft` | POST | Refine draft |
| `/api/antigravity/analyze/full` | POST | Run full pipeline |

### Request Format (example):
```json
{
    "text": "Your research/patent text here...",
    "title": "Project Title",
    "project_type": "research"  // or "patent"
}
```

---

## 🎨 Frontend Components

### Key Files:
- `page.tsx`: Main app with panel switching
- `Sidebar.tsx`: Navigation with "Full Analysis" highlighted
- `AntigravityPanel.tsx`: Complete analysis interface (6 tabs)

### Panel Tabs:
1. **Input**: Upload files or paste text
2. **Concepts**: View extracted terms
3. **Prior Art**: See risk assessment
4. **Summary**: Read structured summary
5. **Refine**: Get improved draft
6. **Full Analysis**: Run everything at once

---

## 🔒 ANTIGRAVITY Safety Rules

These rules are enforced throughout the system:

1. **Evidence-Locked**: All outputs must be traceable to input text
2. **No Fabrication**: Never invent data, results, or citations
3. **No Exaggeration**: Don't overstate novelty or impact
4. **Hedging Language**: Use "appears to", "suggests", "may"
5. **Crash Logs**: On failure, provide structured error info
6. **Claim Preservation**: Never alter or remove user's claims

---

## 🐛 Troubleshooting

### API Returns 429 Error
- **Cause**: Gemini API quota exceeded (20 requests/day on free tier)
- **Fix**: Wait for quota reset or use paid tier

### Frontend Not Loading
```bash
cd frontend
npm install
npm run dev
```

### Backend Errors
```bash
cd backend
pip install -r requirements.txt
# Check .env file has GEMINI_API_KEY
```

---

## 📁 Key Files to Know

| File | What It Does |
|------|--------------|
| `backend/app/main.py` | FastAPI app entry point |
| `backend/app/config.py` | Environment configuration |
| `backend/app/api/routes/antigravity.py` | All ANTIGRAVITY endpoints |
| `backend/app/services/slm_engine.py` | Gemini API wrapper |
| `frontend/src/app/page.tsx` | Main frontend page |
| `frontend/src/components/panels/AntigravityPanel.tsx` | Analysis UI |
