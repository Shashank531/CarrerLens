# CareerLens — Fuzzy Logic Career Recommendation System

CareerLens is an intelligent, full-stack career guidance and learning trajectory mapping platform powered by a 20-trait **Mamdani Fuzzy Inference Engine**. It replaces legacy binary vocational quizzes with continuous psychometric modeling, multi-factor requirement satisfaction, and personalized milestone roadmaps across 105 contemporary professions.

---

## 1. Project Overview

- **Fuzzy Inference Engine**: Evaluates 20 master human skills mapped to 105 careers using 420 domain-expert Mamdani rules and Centroid Defuzzification.
- **Continuous Trajectory Mapping**: Calculates explicit skill deficits (`Gap = Benchmark - User Score`) and structures 6-stage prerequisite-aware curricula from `roadmaps.csv`.
- **Interactive Web Interface**: Semantic HTML5, vanilla CSS custom tokens, Three.js 4,300-particle morphing WebGL canvas, Chart.js radar & bar analytics, and ambient focus audio.
- **Robust Persistence**: SQLite embedded database (`careerlens.db`) operating with **Write-Ahead Logging (WAL)** mode for high concurrent throughput.
- **Offline & Multi-Device Draft Saving**: Auto-saves in-progress assessment responses to prevent data loss.

---

## 2. Directory Structure

```
.
├── backend/
│   ├── app.py                   # Flask REST API, CORS, PDF Generation, CSV API
│   ├── database.py              # SQLite ORM, WAL Mode, Schema Migrations, Drafts
│   ├── userdata_exporter.py     # Real-Time SQLite to User & Attempt CSV Exporter
│   ├── feature_extraction.py    # Likert [1-5] to [0.0-10.0] Formula Normalization
│   ├── fuzzy_engine.py          # Fuzzification, skfuzzy Mamdani Engine, Centroid Defuzzification
│   ├── recommendation_engine.py # Top-N Selection & Plain-Language Match Justifications
│   ├── skill_gap_analysis.py    # Benchmark Matrix Comparison & Deficit Analysis
│   ├── roadmap_builder.py       # Curriculum Assembly & Priority Gap Annotation
│   ├── test_all_personas.py     # 52-Persona System-Wide Stress Test (100% Pass)
│   ├── test_api_suite.py        # End-to-End API Integration & PDF Validation Suite
│   ├── test_eval_integration.py # Evaluation Subsystem Integration Test Suite
│   ├── test_frontend_assets.py  # Frontend Static Assets & Route Integrity Test
│   └── test_pipeline.py         # Automated Validation Suite (5 Archetypal Profiles)
├── data/
│   ├── userdata/
│   │   ├── userdata.csv         # Aggregated User History, Total/Last Attempts, Scores, Codes
│   │   └── user_attempts.csv    # Granular Assessment-by-Assessment History & Top Matches
│   ├── evaluation/
│   │   ├── ground_truth_demo.csv # 105-Career Benchmark Ground Truth Dataset
│   │   └── ground_truth.csv      # Empirical Verified Alumni Placement Dataset
│   └── csv/
│       ├── careers.csv          # 105 Careers Master Catalog & Socio-Economic Indicators
│       ├── career_descriptions.csv  # Detailed Qualitative Roles, Tools, Companies, Scope
│       ├── career_skill_matrix.csv  # 105 Careers x 20 Skill Benchmark Requirements
│       ├── questions.csv        # 70 Psychometric Items across 5 Modules
│       ├── roadmaps.csv         # 630 Step Curricula (6 Steps per Career)
│       └── rules.csv            # 420 Mamdani Inference Rules
├── evaluation/
│   ├── evaluate_recommendations.py # Core IR Evaluation & Ranking Metrics Engine
│   └── results.csv                 # Tabular Benchmark Prediction Output Table
├── frontend/
│   ├── index.html               # Editorial Landing Page & 3D Three.js Constellation
│   ├── login.html               # Dual Authentication Hub & Mnemonic Code Generator
│   ├── assessment.html          # 70-Question 5-Module Assessment with Draft Auto-Save
│   ├── results.html             # Top 5 Cards, Top 30 Drawer, Gaps, Roadmaps, Career Explorer
│   ├── dashboard.html           # 20-Skill Radar Chart, Top 5 Bar Chart, Attempt Timeline
│   ├── js/
│   │   ├── config.js            # Centralized API Configuration (window.CAREERLENS_CONFIG)
│   │   ├── api.js               # Unified Backend Client Service (CareerAPI)
│   │   ├── music.js             # Continuous Web Audio Player with State Sync
│   │   ├── constellation.js     # 3D Skill Node Graph
│   │   └── theme.js             # Dark / Light Theme Synchronizer
│   └── css/
│       ├── theme.css            # Palette Variables, Typography, Tokens
│       ├── landing.css          # Landing Page Layout
│       ├── assessment.css       # Quiz Styles & Animations
│       └── music.css            # Audio Player Layout
├── docs/
│   ├── complete_viva_examiner_qa_handbook.md # Master Examiner, Judge & Viva Defense Handbook
│   ├── whole_project_code_explained.md      # Comprehensive Code & Mathematical Documentation
│   ├── presentation_notes.md                # Viva & Live Demonstration Script
│   ├── evaluation.md                        # Evaluation & IR Retrieval Framework
│   ├── report.md                            # Comprehensive Academic Project Report
│   └── README.md                            # System Documentation & Getting Started Guide
├── serve_frontend.py            # Local Multi-Threaded CORS Server with Dynamic Porting
└── README.md                    # Root Documentation
```

---

## 3. Quick Start & Execution

### Prerequisites
- Python 3.9+
- Python packages: `flask`, `flask-cors`, `scikit-fuzzy`, `numpy`, `reportlab`, `matplotlib`

```bash
pip install flask flask-cors scikit-fuzzy numpy reportlab matplotlib
```

### Running Locally

1. **Start the Flask Backend** (Port 5000):
   ```bash
   python backend/app.py
   ```

2. **Open the Application**:
   - Landing Page: `http://localhost:5000/` or `http://localhost:8000/index.html`
   - Assessment & Results: `http://localhost:5000/login.html`
   - Evaluation Dashboard: `http://localhost:5000/evaluation`

3. **Run Automated Test & Evaluation Suites**:
   ```bash
   # 1. 52-Persona System-Wide Multi-Archetype Stress Test (100% Pass)
   python backend/test_all_personas.py

   # 2. Full 105-Career Benchmark Evaluation Suite
   python evaluation/evaluate_recommendations.py

   # 3. Full API & Integration Suite (Auth, Drafts, Scoring, PDF)
   python backend/test_api_suite.py

   # 4. Pipeline Validation Test (5 Functional Archetypes)
   python backend/test_pipeline.py

   # 5. Evaluation Subsystem Integration Test
   python backend/test_eval_integration.py

   # 6. Frontend Assets & Integrity Test
   python backend/test_frontend_assets.py
   ```

---

## 4. Benchmark Accuracy & Evaluation Performance

| Evaluation Metric | Full Catalog Benchmark (105 Careers) | 52-Persona System Test |
| :--- | :---: | :---: |
| **Top-1 Exact String Match** | **65.71%** (69 / 105) | **—** |
| **Top-5 Recommendation Hit Rate** | **92.38%** (97 / 105) | **100.0%** (52 / 52) |
| **Top-5 Flexible Match Rate** | **96.19%** (101 / 105) | **100.0%** (52 / 52) |
| **Domain Category Alignment** | **84.76%** (89 / 105) | **100.0%** (52 / 52) |
| **Top-5 Domain Alignment** | **99.05%** (104 / 105) | **100.0%** (52 / 52) |
| **Mean Reciprocal Rank (MRR)** | **0.7788** | **0.9620** |
| **Average Target Career Rank** | **#1.89** in 105 careers | **#1.04** in 105 careers |

---

## 5. Master Documentation Index

- **[Complete End-to-End Web & Backend Workflow](end_to_end_web_and_backend_workflow.md)** — Step-by-step technical breakdown of every page, click, button, route, SQLite query, and math algorithm.
- **[Master Examiner, Judge & Viva Defense Handbook](complete_viva_examiner_qa_handbook.md)** — Exhaustive 35+ Q&A covering datasets, backend, math, and evaluation.
- **[Whole Project Code & Formulas Explained](whole_project_code_explained.md)** — In-depth line-by-line python code and mathematical formulations.
- **[Evaluation & Accuracy Framework](evaluation.md)** — Comprehensive IR ranking and benchmark methodologies.
- **[Presentation & Viva Quick Reference Notes](presentation_notes.md)** — Elevator pitch and killer one-liner examiner answers.

---

## 6. Complete API Route Map

| Method | Route | Description |
| :--- | :--- | :--- |
| `POST` | `/api/register` | Create student account and generate unique mnemonic login code |
| `POST` | `/api/login` | Authenticate student via code and retrieve historical attempts |
| `POST` | `/api/assessment/draft` | Auto-save in-progress assessment draft responses |
| `GET`  | `/api/assessment/draft/<id>`| Retrieve in-progress draft responses for an uncompleted assessment |
| `POST` | `/api/submit` | Run analytical fuzzy pipeline, persist result set, and sync CSV |
| `GET`  | `/api/results/<id>` | Fetch most recent assessment result for a user |
| `GET`  | `/api/assessment/<id>/results` | Fetch results for a specific historical assessment attempt |
| `GET`  | `/api/user/<id>/history` | Chronological assessment history and top recommendation badges |
| `GET`  | `/api/careers` | 105-career master catalog JSON with salary, demand, and education |
| `GET`  | `/api/userdata/csv` | Download real-time updated `userdata.csv` with attempt summaries |
| `GET`  | `/api/userdata/attempts/csv` | Download granular attempt-by-attempt history CSV (`user_attempts.csv`) |
| `GET`  | `/api/userdata/export` | Trigger on-demand regeneration and return export metrics |
| `GET`  | `/api/pdf/<id>` | Download ReportLab multi-page summary PDF for latest assessment |
| `GET`  | `/api/pdf/assessment/<id>` | Download ReportLab PDF for a specific assessment attempt |
| `GET`  | `/api/health` | Backend operational liveness probe |
