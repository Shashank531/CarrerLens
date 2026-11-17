# CareerLens — Precision Cognitive AI Career Recommendation System

CareerLens is a state-of-the-art vocational intelligence platform that models human aptitude across **20 continuous master skills** using **Mamdani Fuzzy Logic Inference (Centroid Defuzzification)** blended with **Pearson Profile Shape Correlation** and **Confidence-Weighted Deficit Penalties** across **105 contemporary professions**.

---

## 🌟 Key Highlights & Capabilities
- **Continuous 20-Skill Psychometric Modeling**: Evaluates 70 Likert survey items without reductive binary categorization.
- **Precision Mamdani Fuzzy Core**: 420 domain inference rules with 5 input membership sets (*Very Low* to *Very High*) and 4 output compatibility sets (*Low* to *Excellent*).
- **Fit-Preserving Exponential Scaling**: Dynamic fit-gap scaling ($\text{norm\_s}^{1.5}$) that preserves natural competence distances without artificial rank decay distortion.
- **Automated Skill Deficit Quantification**: Computes required benchmark gaps ($\Delta = r - u$) with priority tagging.
- **Prerequisite-Aware Learning Curricula**: 6-phase career roadmaps with live task checkboxes, progress tracking, and Notion/Markdown export.
- **Interactive "What-If?" Simulation Lab**: Real-time 60fps trait sliders allowing users to simulate future trajectories across 105 careers.
- **Interactive 105-Career Explorer & Comparator**: Multi-parameter side-by-side comparison dock analyzing salaries, demand, and education.
- **Publication-Quality PDF Reports**: Vectorized multi-page PDF generation via ReportLab.
- **Editorial UX & Ambient Audio**: Custom cursor, Three.js 4,300-particle WebGL lattice, Chart.js radar & bar analytics, and ambient focus soundscapes.

---

## 🛠️ Technology Stack
- **Backend Service Layer**: Python 3.9+, Flask, Flask-CORS, SQLite (WAL mode)
- **AI & Fuzzy Modeling**: `scikit-fuzzy`, `numpy` (Mamdani Min-Max & Centroid Defuzzification)
- **PDF Engine**: `reportlab` (Vectorized layouts, tables, and flowables)
- **Frontend Architecture**: Semantic HTML5, Vanilla CSS Design System, Modern ES6+ JavaScript
- **Data Visualization & Graphics**: `Chart.js` (20-skill Radar & Top-5 Bar), `Three.js` (WebGL 3D Interactive Particle Field)

---

## 📂 Project Architecture

```text
├── backend/
│   ├── app.py                   # REST API Orchestration, Sessions, PDF Generator, CSV API
│   ├── database.py              # SQLite Persistence Layer (WAL Mode, Parameterized SQL)
│   ├── userdata_exporter.py     # Real-Time SQLite to User & Attempt CSV Exporter
│   ├── feature_extraction.py    # Likert Normalization (1-5 -> 0-10) & Confidence Metrics
│   ├── fuzzy_engine.py          # Mamdani Inference, Defuzzification & Matrix Precision
│   ├── recommendation_engine.py # Ranking, Trait-Based Explanations & Socio-Economic Metadata
│   ├── skill_gap_analysis.py    # Deficit Quantification & Priority Classification
│   ├── roadmap_builder.py       # 6-Stage Chronological Learning Curricula Ingestion
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
│       ├── career_descriptions.csv  # Detailed Qualitative Roles, Tools, Scope
│       ├── career_skill_matrix.csv  # 105 Careers x 20 Skill Benchmark Requirements
│       ├── questions.csv        # 70 Psychometric Items across 5 Modules
│       ├── roadmaps.csv         # 630 Step Curricula (6 Steps per Career)
│       └── rules.csv            # 420 Mamdani Inference Rules
├── evaluation/
│   ├── evaluate_recommendations.py # Core IR Evaluation & Ranking Metrics Engine
│   └── results.csv                 # Tabular Benchmark Prediction Output Table
├── frontend/
│   ├── index.html               # Landing Page & 3D Three.js Constellation
│   ├── login.html               # Dual Authentication Hub & Mnemonic Code Generator
│   ├── assessment.html          # 70-Question 5-Module Assessment with Draft Auto-Save
│   ├── results.html             # Top 5 Cards, Gaps, Roadmaps, Career Explorer, What-If Lab
│   ├── dashboard.html           # 20-Skill Radar Chart, Top 5 Bar Chart, Evolution Tracker
│   ├── js/                      # Config, API Client, Music, Constellation, Theme
│   └── css/                     # Design System, Music Player, Responsive Tokens
├── docs/
│   ├── end_to_end_web_and_backend_workflow.md # Complete Page-by-Page & Backend Flow Guide
│   ├── complete_viva_examiner_qa_handbook.md  # Master Examiner, Judge & Viva Defense Handbook
│   ├── whole_project_code_explained.md       # Exhaustive Code & Mathematical Defense Guide
│   ├── presentation_notes.md                 # Quick Reference Viva Pitch & Formulas
│   ├── evaluation.md                         # IR Evaluation Metrics (MRR, Top-5 Hit Rate)
│   └── report.md                             # Full Academic Project Report
├── serve_frontend.py            # Local Multi-Threaded CORS Server with Dynamic Porting
└── README.md                    # System Documentation
```

---

## 🚀 Getting Started & Execution

### 1. Install Dependencies
```bash
pip install flask flask-cors scikit-fuzzy numpy reportlab matplotlib
```

### 2. Launch the Backend API (Port 5000)
```bash
python backend/app.py
```

### 3. Access the Application
- **Editorial Landing**: `http://localhost:5000/` or `http://localhost:8000/index.html`
- **Assessment / Login**: `http://localhost:5000/login.html`
- **Evaluation Dashboard**: `http://localhost:5000/evaluation`

---

## 🧪 Mathematical Verification, Benchmarks & Test Suites

Run the automated test suites:
```bash
# 1. 52-Persona System-Wide Multi-Archetype Stress Test (100% Pass)
python backend/test_all_personas.py

# 2. Complete 105-Career Benchmark Evaluation Suite
python evaluation/evaluate_recommendations.py
```

Run the pipeline functional unit tests:
```bash
python backend/test_pipeline.py
```

---

## 📊 Benchmark Evaluation Summary (105-Career Catalog)

- **Top-5 Hit Rate**: **92.38%** (97 / 105 careers placed in Top 5)
- **Top-5 Flexible Match**: **96.19%** (101 / 105 in candidate choice set)
- **Domain Category Alignment**: **84.76%** (Top-1) / **99.05%** (Top-5)
- **Mean Reciprocal Rank (MRR)**: **0.7788**
- **Average Target Career Rank**: **#1.89** out of 105 careers

---
*CareerLens — Precision Fuzzy Cognitive AI Vocational Guidance & Career OS.*
