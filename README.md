# Inventix AI
## Evidence-Locked Research & Patent Intelligence Platform

<div align="center">

![Inventix AI](https://img.shields.io/badge/Inventix-AI-6366f1?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBvbHlnb24gcG9pbnRzPSIxMyAyIDMgMTQgMTIgMTQgMTEgMjIgMjEgMTAgMTIgMTAgMTMgMiIvPjwvc3ZnPg==)
![Python](https://img.shields.io/badge/Python-3.11+-3776ab?style=for-the-badge&logo=python&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-14+-000000?style=for-the-badge&logo=next.js&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini-AI-4285f4?style=for-the-badge&logo=google&logoColor=white)

**ANTIGRAVITY: A constrained intelligence system that treats uncertainty as a first-class signal.**

[Problem](#problem-statement) • [Architecture](#architecture) • [Tech Stack](#tech-stack) • [Setup](#setup-instructions) • [AI Tools](#ai-tools-used) • [Prompts](#prompt-strategy) • [Output](#final-output)

</div>

---

## Problem Statement

### The Innovation Intelligence Gap

Modern researchers, innovators, and R&D teams face critical challenges in the innovation lifecycle:

| Problem | Impact |
|---------|--------|
| **Fragmented Research Tools** | Time wasted switching between disconnected platforms |
| **Manual Prior-Art Searches** | Hours of manual patent database queries with uncertain coverage |
| **Unclear Novelty Signals** | No objective way to assess if an idea is truly novel |
| **AI Hallucinations** | Generic AI tools fabricate citations and invent false claims |
| **Lack of End-to-End Visibility** | No unified view from idea conception to publication |
| **Legal Uncertainty** | Researchers cannot distinguish AI speculation from evidence |

### Our Solution: ANTIGRAVITY

**Inventix AI** introduces ANTIGRAVITY — a constrained intelligence system that:

- ✅ **Never invents facts** — Every statement references an evidence ID
- ✅ **Embraces uncertainty** — Returns "UNKNOWN" instead of guessing
- ✅ **Produces structured outputs** — JSON schemas, not free-form prose
- ✅ **Generates probabilistic signals** — Indicators, not conclusions
- ✅ **Maintains audit trails** — Every output is reproducible and traceable

> **Key Insight**: The model is never trusted. The pipeline is.

---

## Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              INVENTIX AI                                     │
│                    Evidence-Locked Intelligence Platform                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────────────────────────────────────────┐    │
│  │   FRONTEND  │    │                   BACKEND                        │    │
│  │  (Next.js)  │    │                  (FastAPI)                       │    │
│  │             │    │                                                  │    │
│  │ ┌─────────┐ │    │  ┌──────────────────────────────────────────┐   │    │
│  │ │Dashboard│ │◄──►│  │              API LAYER                   │   │    │
│  │ └─────────┘ │    │  │  /api/analysis  /api/patent  /api/research│   │    │
│  │ ┌─────────┐ │    │  └──────────────────────────────────────────┘   │    │
│  │ │  Idea   │ │    │                      │                          │    │
│  │ │Analyzer │ │    │                      ▼                          │    │
│  │ └─────────┘ │    │  ┌──────────────────────────────────────────┐   │    │
│  │ ┌─────────┐ │    │  │           ANTIGRAVITY CORE               │   │    │
│  │ │ Patent  │ │    │  │  ┌────────────┐  ┌────────────────────┐  │   │    │
│  │ │  Risk   │ │    │  │  │ SLM Engine │  │ Evidence Validator │  │   │    │
│  │ └─────────┘ │    │  │  │  (Gemini)  │  │  (Crash on Fail)   │  │   │    │
│  │ ┌─────────┐ │    │  │  └────────────┘  └────────────────────┘  │   │    │
│  │ │Research │ │    │  │  ┌────────────┐  ┌────────────────────┐  │   │    │
│  │ │ Engine  │ │    │  │  │  Schema    │  │   Audit Logger     │  │   │    │
│  │ └─────────┘ │    │  │  │ Validator  │  │  (Immutable Logs)  │  │   │    │
│  │ ┌─────────┐ │    │  │  └────────────┘  └────────────────────┘  │   │    │
│  │ │Knowledge│ │    │  └──────────────────────────────────────────┘   │    │
│  │ │  Graph  │ │    │                      │                          │    │
│  │ └─────────┘ │    │                      ▼                          │    │
│  └─────────────┘    │  ┌──────────────────────────────────────────┐   │    │
│                     │  │            EXTERNAL SERVICES              │   │    │
│                     │  │  ┌──────────┐  ┌──────────┐  ┌─────────┐  │   │    │
│                     │  │  │ Google   │  │ Patent   │  │ Academic│  │   │    │
│                     │  │  │ Gemini   │  │   APIs   │  │   APIs  │  │   │    │
│                     │  │  │   API    │  │ (Future) │  │ (Future)│  │   │    │
│                     │  │  └──────────┘  └──────────┘  └─────────┘  │   │    │
│                     │  └──────────────────────────────────────────┘   │    │
│                     └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
User Input → Validation → Evidence Check → SLM Reasoning → Output Validation → Response
     │            │              │               │                │              │
     │            │              │               │                │              │
     └── CRASH ◄──┴── CRASH ◄────┴── CRASH ◄─────┴── CRASH ◄──────┘              │
         LOG          LOG            LOG             LOG                         │
                                                                                 │
                                              ┌──────────────────────────────────┘
                                              ▼
                                    Structured JSON Response
                                    + Evidence References
                                    + Confidence Level
                                    + Scope Disclaimer
                                    + Unknowns List
```

---

## Tech Stack

### Backend

| Technology | Purpose | Version |
|------------|---------|---------|
| **Python** | Core runtime | 3.11+ |
| **FastAPI** | REST API framework | Latest |
| **Pydantic** | Data validation & schemas | v2 |
| **Uvicorn** | ASGI server | Latest |
| **Google Generative AI** | Gemini API client | Latest |

### Frontend

| Technology | Purpose | Version |
|------------|---------|---------|
| **Next.js** | React framework | 14+ |
| **React** | UI library | 18+ |
| **TypeScript** | Type safety | 5+ |
| **Framer Motion** | Animations | Latest |
| **Recharts** | Data visualization | Latest |
| **Lucide React** | Icons | Latest |
| **CSS Modules** | Component styling | Native |

### AI / ML

| Technology | Purpose |
|------------|---------|
| **Google Gemini 1.5 Flash** | Primary SLM for structured reasoning |
| **Evidence-Locked Prompting** | Custom prompt architecture for grounded outputs |

### Infrastructure

| Technology | Purpose |
|------------|---------|
| **npm** | Package management (frontend) |
| **pip** | Package management (backend) |
| **Git** | Version control |

---

## Setup Instructions

### Prerequisites

- **Python** 3.11 or higher
- **Node.js** 18 or higher
- **npm** 9 or higher
- **Git**
- **Google Gemini API Key** (get one at https://aistudio.google.com/)

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd inventix-ai
```

### Step 2: Configure Environment Variables

Create or edit the `.env` file in the project root:

```env
# Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash

# Backend Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
DEBUG=true

# Frontend Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=Inventix AI
```

### Step 3: Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
```

### Step 5: Run the Application

**Terminal 1 - Backend:**
```bash
cd backend
.\venv\Scripts\activate  # Windows
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Step 6: Access the Application

| Service | URL |
|---------|-----|
| **Frontend Dashboard** | http://localhost:3000 |
| **Backend API** | http://localhost:8000 |
| **API Documentation** | http://localhost:8000/docs |
| **ReDoc** | http://localhost:8000/redoc |

---

## AI Tools Used

### Primary AI: Google Gemini 1.5 Flash

| Aspect | Details |
|--------|---------|
| **Model** | `gemini-1.5-flash` |
| **Provider** | Google AI Studio |
| **Use Case** | Structured reasoning, concept extraction, novelty scoring |
| **Temperature** | 0.3 (low for determinism) |
| **Output Format** | JSON only (enforced) |

### Why Gemini?

1. **Speed**: Flash model optimized for fast inference
2. **Cost**: Lower cost than GPT-4 while maintaining quality
3. **Structured Output**: Excellent JSON compliance
4. **Context Window**: Large context for comprehensive analysis

### ANTIGRAVITY Wrapper

The SLM engine wraps Gemini with:

```python
# Evidence-locking enforcement
- System prompt injection with ANTIGRAVITY rules
- JSON parsing with fallback handling
- Evidence reference validation
- Crash log generation on failure
```

---

## Prompt Strategy

### Core Philosophy: Evidence-Locked Reasoning

Our prompt strategy enforces the ANTIGRAVITY behavioral contract:

```
┌─────────────────────────────────────────────────────────────┐
│                  PROMPT ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. SYSTEM PROMPT (Behavioral Contract)                     │
│     ├── Identity: "You are ANTIGRAVITY..."                  │
│     ├── Rules: Evidence-first, no hallucination             │
│     └── Output: JSON only, structured schemas               │
│                                                             │
│  2. EVIDENCE BLOCK                                          │
│     ├── [EVD-001]: User input                               │
│     ├── [EVD-002]: Retrieved context (if any)               │
│     └── [EVD-XXX]: Additional sources                       │
│                                                             │
│  3. TASK PROMPT                                             │
│     ├── Clear objective                                     │
│     ├── Required output schema                              │
│     └── Explicit constraints                                │
│                                                             │
│  4. SAFETY RAILS                                            │
│     ├── "If uncertain, return UNKNOWN"                      │
│     ├── "Do NOT assess patentability"                       │
│     └── "All scores are probabilistic estimates"            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Example Prompt Structure

```python
SYSTEM_PROMPT = """
You are ANTIGRAVITY, an evidence-locked analysis system.
Output only valid JSON. Never invent facts.
"""

TASK_PROMPT = f"""
Analyze this innovation idea and extract structured information.

IDEA: {user_input}
DOMAIN: {domain}

You must respond in valid JSON with this exact structure:
{{
    "idea_summary": "A concise 2-3 sentence summary",
    "key_concepts": ["concept1", "concept2"],
    "novelty_indicators": {{
        "overall_score": 0.0 to 1.0,
        "semantic_uniqueness": 0.0 to 1.0,
        "prior_art_risk": 0.0 to 1.0
    }},
    "potential_overlaps": ["area1", "area2"],
    "recommended_searches": ["search1", "search2"]
}}

IMPORTANT:
- Scores are PROBABILISTIC ESTIMATES, not definitive
- If uncertain, bias scores toward 0.5 (unknown)
- Do not claim patentability or legal conclusions
"""
```

### Prompt Engineering Techniques Used

| Technique | Implementation |
|-----------|----------------|
| **Role Assignment** | "You are ANTIGRAVITY..." establishes constrained persona |
| **Output Schema Enforcement** | Explicit JSON structure in prompt |
| **Negative Constraints** | "Do NOT...", "Never..." rules |
| **Uncertainty Acknowledgment** | Explicit "UNKNOWN" fallback instruction |
| **Evidence Grounding** | Evidence IDs must be referenced |
| **Temperature Control** | Low temperature (0.3) for consistency |

---

## Source Code

### Project Structure

```
inventix-ai/
│
├── .env                              # Environment configuration
├── .gitignore                        # Git ignore rules
├── README.md                         # This file
├── README_Inventix_AI_VISION.md      # Original vision document
│
├── backend/                          # Python FastAPI backend
│   ├── requirements.txt              # Python dependencies
│   ├── venv/                         # Virtual environment
│   └── app/
│       ├── __init__.py
│       ├── main.py                   # FastAPI application entry
│       ├── config.py                 # Pydantic settings
│       │
│       ├── api/
│       │   ├── __init__.py           # API router aggregation
│       │   └── routes/
│       │       ├── __init__.py
│       │       ├── analysis.py       # Idea analysis endpoints
│       │       ├── patent.py         # Patent risk scanning
│       │       ├── research.py       # Research engine (placeholder)
│       │       └── knowledge.py      # Knowledge graph (placeholder)
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   └── schemas.py            # ANTIGRAVITY-compliant schemas
│       │
│       └── services/
│           ├── __init__.py
│           └── slm_engine.py         # Gemini API integration
│
├── frontend/                         # Next.js frontend
│   ├── package.json
│   ├── next.config.ts
│   ├── tsconfig.json
│   ├── .env.local                    # Frontend env vars
│   │
│   └── src/
│       ├── app/
│       │   ├── globals.css           # Design system
│       │   ├── layout.tsx            # Root layout
│       │   ├── page.tsx              # Main page
│       │   └── page.module.css
│       │
│       └── components/
│           ├── Header.tsx            # App header
│           ├── Header.module.css
│           ├── Sidebar.tsx           # Navigation sidebar
│           ├── Sidebar.module.css
│           │
│           └── panels/
│               ├── DashboardOverview.tsx    # Dashboard
│               ├── DashboardOverview.module.css
│               ├── IdeaAnalyzer.tsx         # Idea analysis panel
│               ├── IdeaAnalyzer.module.css
│               ├── PatentRiskPanel.tsx      # Patent risk scanner
│               ├── PatentRiskPanel.module.css
│               ├── ResearchPanel.tsx        # Research (placeholder)
│               ├── ResearchPanel.module.css
│               ├── KnowledgeGraphPanel.tsx  # Knowledge graph
│               └── KnowledgeGraphPanel.module.css
│
└── docs/
    └── ANTIGRAVITY_SYSTEM_SPEC.md    # AI behavioral specification
```

### Key Source Files

#### Backend: SLM Engine (`backend/app/services/slm_engine.py`)
- Wraps Google Gemini API
- Enforces JSON output parsing
- Implements evidence-locking
- Generates crash logs on failure

#### Backend: Schemas (`backend/app/core/schemas.py`)
- Pydantic models for ANTIGRAVITY compliance
- CrashLog schema for failure handling
- EvidenceReference schema for audit trails

#### Frontend: Design System (`frontend/src/app/globals.css`)
- Premium dark mode color palette
- Glassmorphism effects
- Animation utilities
- Component styles

---

## Final Output

### Application Screenshots

The application provides:

1. **Dashboard Overview**
   - System status indicators
   - Quick stats (placeholder for future data)
   - Welcome message with feature highlights
   - Legal disclaimer prominently displayed

2. **Idea Analyzer Panel**
   - Text input for innovation ideas
   - Domain and context fields
   - Real-time novelty scoring
   - Key concept extraction
   - Potential overlap detection
   - Recommended search queries
   - ANTIGRAVITY-compliant outputs with evidence references

3. **Patent Risk Scanner**
   - Claim text analysis
   - Radar chart visualization
   - Risk breakdown (novelty, scope, clarity, prior art)
   - Overall risk gauge
   - Detailed disclaimers

4. **Research Engine** (Placeholder)
   - Planned features displayed
   - Integration roadmap

5. **Knowledge Graph Explorer** (Placeholder)
   - Demo visualization
   - Future capabilities outlined

### API Responses

All API responses follow the ANTIGRAVITY schema:

```json
{
  "idea_summary": "Evidence-grounded summary...",
  "key_concepts": ["concept1", "concept2"],
  "novelty_indicators": {
    "overall_score": 0.65,
    "semantic_uniqueness": 0.72,
    "domain_coverage": 0.58,
    "prior_art_risk": 0.45
  },
  "evidence_references": [
    {
      "evidence_id": "EVD-20260201123456-INPUT",
      "source": "user_input",
      "timestamp": "2026-02-01T12:34:56Z"
    }
  ],
  "confidence": "medium",
  "scope_disclaimer": "This analysis provides probabilistic indicators only...",
  "unknowns": ["Actual prior art overlap", "Patent claim conflicts"]
}
```

---

## Build Reproducibility Instructions

### Complete Reproducibility Steps

Follow these exact steps to reproduce the build from scratch:

#### 1. System Requirements

```bash
# Verify Python version (must be 3.11+)
python --version

# Verify Node.js version (must be 18+)
node --version

# Verify npm version (must be 9+)
npm --version
```

#### 2. Clone and Setup

```bash
# Clone repository
git clone <repository-url>
cd inventix-ai

# Create .env file with your Gemini API key
echo "GEMINI_API_KEY=your_key_here" > .env
echo "GEMINI_MODEL=gemini-1.5-flash" >> .env
echo "BACKEND_HOST=0.0.0.0" >> .env
echo "BACKEND_PORT=8000" >> .env
echo "DEBUG=true" >> .env
```

#### 3. Backend Setup (Exact Commands)

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Activate (Linux/Mac)
# source venv/bin/activate

# Install exact dependencies
pip install fastapi uvicorn python-dotenv google-generativeai pydantic pydantic-settings httpx python-multipart

# Verify installation
pip list
```

#### 4. Frontend Setup (Exact Commands)

```bash
# Navigate to frontend
cd ../frontend

# Install dependencies
npm install

# Verify installation
npm list --depth=0
```

#### 5. Run Application

```bash
# Terminal 1: Backend
cd backend
.\venv\Scripts\activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

#### 6. Verify Build

| Check | Expected Result |
|-------|-----------------|
| Backend health | `curl http://localhost:8000/` returns JSON with status |
| API docs | http://localhost:8000/docs loads Swagger UI |
| Frontend | http://localhost:3000 loads dashboard |
| Idea analysis | POST to `/api/analysis/idea` returns structured JSON |

#### 7. Dependency Versions (For Exact Reproduction)

**Backend (`pip freeze` output):**
```
fastapi>=0.109.0
uvicorn>=0.27.0
python-dotenv>=1.0.0
google-generativeai>=0.3.2
pydantic>=2.5.0
pydantic-settings>=2.1.0
httpx>=0.26.0
python-multipart>=0.0.6
```

**Frontend (`package.json` dependencies):**
```json
{
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.0.0",
    "react-dom": "^18.0.0",
    "framer-motion": "^10.0.0",
    "recharts": "^2.0.0",
    "lucide-react": "^0.300.0",
    "axios": "^1.6.0"
  }
}
```

### Troubleshooting

| Issue | Solution |
|-------|----------|
| `pydantic-core` build fails | Ensure Python 3.11+ and latest pip: `pip install --upgrade pip` |
| Frontend port conflict | Change port: `npm run dev -- -p 3001` |
| Backend port conflict | Change port in uvicorn command: `--port 8001` |
| Gemini API errors | Verify API key in `.env` file |
| CORS errors | Ensure backend is running on port 8000 |

---

## License

MIT License

---

## Contributors

Built for Hackathon 2026

---

<div align="center">

**Inventix AI: Where Evidence Meets Intelligence**

*Accuracy > Coverage • Evidence > Eloquence • Transparency > Usefulness*

</div>
