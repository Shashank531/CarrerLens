# CareerLens

> Fuzzy Logic Career Recommendation and Trajectory Mapping System

[![Live Demo](https://img.shields.io/badge/Live%20Demo-carrerlens--a3dl.onrender.com-2ea44f?style=flat-square&logo=render)](https://carrerlens-a3dl.onrender.com)
[![Python Version](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11-3776ab?style=flat-square&logo=python)](https://python.org)
[![Framework](https://img.shields.io/badge/Backend-Flask%20%7C%20Gunicorn-black?style=flat-square&logo=flask)](https://flask.palletsprojects.com/)
[![Database](https://img.shields.io/badge/Database-SQLite%20(WAL)-003b57?style=flat-square&logo=sqlite)](https://sqlite.org)
[![Release](https://img.shields.io/badge/Release-v2.1.0-blue?style=flat-square&logo=github)](https://github.com/Shashank531/CarrerLens)

**Live Web Application:** [https://carrerlens-a3dl.onrender.com](https://carrerlens-a3dl.onrender.com)  
The platform is publicly deployed and accessible directly via any modern web browser without local setup.

---

## Overview

CareerLens is a full-stack career guidance and learning trajectory mapping system developed as an academic engineering project. Traditional career assessment tools often rely on binary questions and rigid categorization (such as basic Myers-Briggs tests or static keyword matching), forcing individuals into narrow buckets.

CareerLens replaces that approach with continuous psychometric modeling. It measures user aptitude across **20 distinct skill dimensions** using a **Mamdani Fuzzy Inference System** combined with **Pearson profile correlation** and deficit-weighted scoring across a curated catalog of **105 modern professions**.

In addition to career matching, the system calculates exact skill gaps (`Δ = Benchmark - User Score`), constructs structured 6-phase learning roadmaps, enables interactive "What-If" career trajectory simulations, and generates downloadable multi-page PDF evaluation reports.

---

## Core Methodology

The scoring pipeline processes user responses through four sequential stages:

```
[70 Likert Items] ──> [Feature Extraction] ──> [Mamdani Fuzzy Inference] ──> [Composite Fit Score] ──> [Ranked Matches]
 (5 Survey Modules)    (20 Skill Dimensions)     (420 Rules + Defuzz)          (Fuzzy + Matrix + Gap)     (Top 5 & 105 Catalog)
```

1. **Psychometric Feature Extraction**  
   The assessment consists of 70 Likert-scale questions (1 to 5) distributed across five modules: Technical, Analytical, Creative, People & Leadership, and Core Aptitude. Responses are normalized to a continuous scale from `0.0` to `10.0`. Questions include reverse-scored controls and confidence weighting based on module coverage.

2. **Mamdani Fuzzy Inference Engine**  
   A domain-specific knowledge base of **420 fuzzy inference rules** maps combinations of input traits to career compatibility.
   - **Input Sets**: 5 overlapping triangular membership functions per trait (*Very Low*, *Low*, *Medium*, *High*, *Very High*).
   - **Output Sets**: 4 triangular compatibility sets (*Low*, *Medium*, *High*, *Excellent*).
   - **Defuzzification**: Centroid (Center of Gravity) method producing a continuous score from `0.0` to `100.0`.

3. **Multi-Factor Profile Matching**  
   To complement rule-based fuzzy inference, the system computes a profile-matrix fit using:
   - **Pearson Profile Correlation**: Compares the shape of the user's skill profile against the benchmark vector of each career (`r ∈ [-1, 1]`), rewarding relative alignment regardless of baseline bias.
   - **Requirement Satisfaction**: Weighted sum where core career requirements carry exponential weight (`(requirement / 10)^2.5`), prioritizing mandatory competencies.
   - **Confidence-Weighted Deficit Penalty**: Penalties applied when a candidate falls significantly short on non-negotiable core skills.

4. **Composite Scoring and Non-Linear Fit Scaling**  
   The final compatibility score blends the fuzzy rule output and matrix correlation:
   ```
   Raw Score = 0.45 * Fuzzy Score + 0.55 * Matrix Score
   ```
   To maintain realistic rank distribution without artificial compression, the score is mapped across a 12% to 96% range using fit-preserving power-law scaling:
   ```
   Normalized Score = (Raw Score - min_raw) / (max_raw - min_raw)
   Compatibility %  = 12.0 + (Normalized Score)^1.5 * (96.0 - 12.0)
   ```

5. **Skill Gap Quantification**  
   For every career, the engine computes explicit deficits:
   ```
   Gap = Required Benchmark - User Score
   ```
   Gaps are classified into actionable categories:
   - `CRITICAL` (`Δ >= 3.0`): Immediate blocker requiring structured intervention.
   - `MODERATE` (`1.5 <= Δ < 3.0`): Key growth area to address during learning.
   - `MINOR` (`0.0 < Δ < 1.5`): Minor enhancement needed.
   - `STRENGTH` (`Δ <= 0.0`): User meets or exceeds the industry requirement.

---

## Key Features

- **Continuous 20-Skill Assessment**: Evaluates technical, analytical, creative, and interpersonal skills across 70 balanced items.
- **Auto-Save Assessment Drafts**: Drafts are continuously synced to local storage and SQLite to prevent progress loss.
- **Top Career Matches with Justifications**: Identifies Top 5 recommendations with plain-language rationales highlighting user signature traits.
- **6-Phase Learning Curricula**: Generates personalized learning paths with prerequisite-aware milestone checklists and time estimates from a database of 630 curated learning steps.
- **Interactive "What-If" Simulation Lab**: Real-time 60fps sliders let users simulate how developing specific skills impacts their fit across all 105 careers.
- **105-Career Comparative Explorer**: Side-by-side comparison dock analyzing market demand, average salary (LPA), required education, and skill profiles.
- **Longitudinal Dashboard**: Visualizes historical attempts, skill evolution over time, and interactive radar/bar charts.
- **Server-Side PDF Generation**: Generates multi-page diagnostic summary reports via ReportLab with embedded charts, gap matrices, and roadmaps.
- **Passwordless Authentication**: Generates unique mnemonic credentials (e.g., `ARJUN-4827`) for simplified returning student login.

---

## Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend Framework** | Python 3.9+, Flask 3.0, Flask-CORS |
| **WSGI Server** | Gunicorn (2 workers, 8 threads, 120s timeout) |
| **Fuzzy Logic & Math** | `scikit-fuzzy`, `numpy`, `scipy` |
| **Document Generation** | `reportlab`, `matplotlib` |
| **Database** | SQLite 3 with Write-Ahead Logging (WAL mode) |
| **Frontend** | Vanilla HTML5, CSS3 (Design Tokens, Dark/Light mode), JavaScript (ES6+) |
| **Data Visualization** | Chart.js (Radar & Bar), Three.js (3D WebGL particle constellation) |
| **Deployment** | Render Web Service |

---

## Repository Structure

```text
.
├── app.py                      # Production WSGI entry point for Gunicorn
├── Procfile                    # Render process declaration
├── render.yaml                 # Render infrastructure specification
├── requirements.txt            # Python package dependencies
├── serve_frontend.py           # Local development server with dynamic port allocation
├── backend/
│   ├── app.py                  # Flask REST API endpoints and request handlers
│   ├── database.py             # SQLite database manager (WAL mode, transactions)
│   ├── feature_extraction.py   # Likert normalization and confidence metric calculations
│   ├── fuzzy_engine.py         # Mamdani inference engine and centroid defuzzification
│   ├── recommendation_engine.py# Composite scoring, ranking, and explanation generator
│   ├── skill_gap_analysis.py   # Benchmark comparison and deficit categorization
│   ├── roadmap_builder.py      # 6-phase curriculum builder from catalog data
│   ├── userdata_exporter.py    # Runtime CSV export utility for assessment records
│   ├── requirements.txt        # Backend dependency mirror
│   └── test_*.py               # Automated testing suites (API, pipeline, stress tests)
├── frontend/
│   ├── index.html              # Landing page with interactive 3D WebGL constellation
│   ├── login.html              # Authentication portal with unique mnemonic code generator
│   ├── assessment.html         # 70-question psychometric survey with autosave
│   ├── results.html            # Match cards, gap analysis, roadmaps, and what-if lab
│   ├── dashboard.html          # Longitudinal progress tracker, radar charts, attempt timeline
│   ├── evaluation.html         # Administrative IR metrics and accuracy dashboard
│   ├── css/                    # Modular stylesheets (theme, landing, assessment, music)
│   ├── js/                     # Client services (API client, config, audio player, charts)
│   └── favicon.png             # Application favicon
├── data/
│   ├── csv/
│   │   ├── careers.csv         # 105-career catalog with market indicators and salaries
│   │   ├── career_descriptions.csv # Qualitative role descriptions, tools, and responsibilities
│   │   ├── career_skill_matrix.csv # 105 careers x 20 skill benchmark requirements
│   │   ├── questions.csv       # 70 psychometric questions across 5 modules
│   │   ├── roadmaps.csv        # 630 curriculum steps (6 phases per career)
│   │   └── rules.csv           # 420 Mamdani fuzzy inference rules
│   └── evaluation/
│       ├── ground_truth_demo.csv# Benchmark profile dataset
│       └── ground_truth.csv     # Verified candidate test vectors
├── evaluation/
│   ├── evaluate_recommendations.py # Information Retrieval (IR) evaluation benchmark script
│   └── results.csv             # Benchmark evaluation output metrics
└── docs/                       # Project report, examiner QA handbook, and technical guides
```

> **Note on Data Privacy:** Student account records and assessment attempt histories stored in SQLite (`careerlens.db`) and exported runtime CSV files are excluded from version control via `.gitignore` to protect personal data.

---

## Getting Started

### Prerequisites

- Python 3.9, 3.10, or 3.11
- Git

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Shashank531/CarrerLens.git
   cd CarrerLens
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Running Locally

Start the application using the Flask development server:
```bash
python backend/app.py
```

The application will start on `http://localhost:5000`:
- **Landing Page**: `http://localhost:5000/`
- **Assessment / Login**: `http://localhost:5000/login.html`
- **Evaluation Dashboard**: `http://localhost:5000/evaluation`

Alternatively, to run the production WSGI configuration locally:
```bash
gunicorn --workers 2 --threads 8 --timeout 120 app:app
```

---

## Testing and Evaluation

The repository includes automated test suites covering the fuzzy engine, API endpoints, and IR ranking accuracy.

### 1. Benchmark Evaluation (105 Careers)
Runs the Information Retrieval evaluation against ground-truth career competency vectors:
```bash
python evaluation/evaluate_recommendations.py
```

### 2. Multi-Persona Stress Test (52 Archetypes)
Tests the recommendation pipeline against 52 diverse student profiles across all career categories:
```bash
python backend/test_all_personas.py
```

### 3. API and Integration Suite
Validates authentication, draft saving, assessment submission, and PDF generation:
```bash
python backend/test_api_suite.py
```

### 4. Pipeline Unit Tests
Verifies mathematical transformations, Likert normalization, and gap calculations:
```bash
python backend/test_pipeline.py
```

---

## Benchmark Results

Evaluation across the 105-career catalog and 52 synthetic archetypal personas yielded the following retrieval metrics:

| Metric | 105-Career Benchmark | 52-Persona System Test | Description |
| :--- | :---: | :---: | :--- |
| **Top-1 Exact Match** | 65.71% (69 / 105) | — | Target career ranked as #1 recommendation |
| **Top-5 Hit Rate** | **92.38%** (97 / 105) | **100.0%** (52 / 52) | Target career placed in Top 5 recommendations |
| **Top-5 Flexible Match** | **96.19%** (101 / 105) | **100.0%** (52 / 52) | Target or closely related occupation in Top 5 |
| **Domain Category Alignment** | 84.76% (89 / 105) | 100.0% (52 / 52) | Top recommendation matches target domain |
| **Top-5 Domain Alignment** | **99.05%** (104 / 105) | **100.0%** (52 / 52) | At least one Top 5 match in target domain |
| **Mean Reciprocal Rank (MRR)**| **0.7788** | **0.9620** | Average reciprocal rank of the target career |
| **Average Target Career Rank**| **#1.89** / 105 | **#1.04** / 105 | Mean position of ground truth career |

---

## API Reference

The backend exposes a clean REST API:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/register` | Register student profile; returns unique login code |
| `POST` | `/api/login` | Authenticate using mnemonic code; returns user history |
| `POST` | `/api/assessment/draft` | Save in-progress assessment draft |
| `GET`  | `/api/assessment/draft/<id>` | Retrieve saved assessment draft for user |
| `POST` | `/api/submit` | Submit 70 answers; runs fuzzy pipeline and persists results |
| `GET`  | `/api/results/<id>` | Fetch most recent assessment results for user |
| `GET`  | `/api/assessment/<id>/results` | Fetch results for a specific historical attempt |
| `GET`  | `/api/user/<id>/history` | Retrieve chronological attempt history and top badges |
| `GET`  | `/api/careers` | Retrieve 105-career catalog with salaries and demand metrics |
| `GET`  | `/api/pdf/<id>` | Download publication-quality diagnostic PDF report |
| `GET`  | `/api/health` | Service health and liveness check |

---

## Documentation

Comprehensive project documentation is available in the `docs/` directory:

- [Academic Project Report](docs/report.md) — Complete methodology, mathematical formulations, literature review, and findings.
- [End-to-End Workflow Guide](docs/end_to_end_web_and_backend_workflow.md) — Detailed technical trace through every screen, API request, database query, and algorithm.
- [Viva & Examiner QA Handbook](docs/complete_viva_examiner_qa_handbook.md) — 35+ technical questions and answers covering datasets, fuzzy logic, and architectural decisions.
- [Code & Mathematical Defense](docs/whole_project_code_explained.md) — Line-by-line breakdown of mathematical functions, fuzzy inference formulas, and algorithms.
- [Evaluation Framework](docs/evaluation.md) — Information Retrieval evaluation metrics and benchmarking methodology.
- [Presentation Notes](docs/presentation_notes.md) — Summary reference guide and demonstration talking points.

---

## Academic Context

- **Project**: Engineering Mini Project (Semester 7)
- **Program**: B.Tech / MBA Tech
- **Core Focus**: Applied Artificial Intelligence, Fuzzy Logic, Decision Support Systems, and Human-Computer Interaction
- **Author**: Shashank ([GitHub](https://github.com/Shashank531))
