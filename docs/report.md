# CareerLens: project report

## 1. Project overview

### 1.1 Problem statement
Most career counseling tools and vocational tests rely on rigid classification systems like MBTI or Holland Codes, or on basic weighted averages. These methods group individuals into mutually exclusive categories or collapse distinct competencies into a single number. In practice, skills such as leadership, logical thinking, adaptability, and creativity exist on continuous, overlapping scales rather than binary pass-or-fail thresholds.

CareerLens is a career recommendation platform built on Mamdani fuzzy inference. The system models 20 core skills across 105 occupations. It processes psychometric assessment responses, computes degree-of-membership values for each skill, evaluates career compatibility through expert-defined rulebases, identifies specific skill gaps, and generates step-by-step learning roadmaps.

### 1.2 Motivation for fuzzy logic
A standard weighted-sum model calculates career match as:

$$\text{Score} = \sum_{i=1}^{n} w_i \cdot s_i$$

Linear scoring has several clear weaknesses for career guidance:

1. Non-linear skill dependencies: Professional success depends on specific combinations of skills. High programming ability without logical thinking or problem-solving yields different career outcomes than programming combined with analytical reasoning. Fuzzy logic captures these relationships using multi-condition rules ($\text{IF } A \text{ AND } B \text{ THEN } C$).
2. Handling subjective inputs: Self-reported Likert scale responses (1 to 5) contain individual calibration differences. Fuzzy sets handle this variance by assigning partial membership across overlapping linguistic categories. For example, a score of 7.2 out of 10 belongs partially to both "Medium" and "High" sets.
3. Deficit sensitivity: Simple averages allow a high score in an irrelevant area to mask a critical deficiency. A candidate with a 10/10 in physical stamina and 1/10 in programming might receive an acceptable average score for software engineering in a linear formula. CareerLens evaluates rule antecedents so that missing core prerequisites directly limits compatibility scores.
4. Traceable reasoning: Mamdani inference evaluates transparent linguistic rules (such as $\text{IF } \text{Programming is Very High AND Math is High THEN AI/ML Compatibility is Excellent}$). This allows the system to generate clear, plain-language explanations for each recommendation.

---

## 2. System architecture

### 2.1 End-to-end data flow
CareerLens separates responsibilities across four layers: a browser frontend, a Flask REST API, analytical processing modules, and an SQLite database.

```
[ User Interaction ]
        │
        ▼
┌──────────────────┐
│  frontend/       │ ── (1) Account registration / unique code login (NAME-1234)
│  login.html      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  frontend/       │ ── (2) 70-question 5-module assessment (Likert 1–5 scale)
│  assessment.html │
└────────┬─────────┘
         │
         ▼  [ HTTP POST /api/submit  { user_id, answers: { Q1: 5, ... } } ]
┌──────────────────┐
│  backend/        │ ── (3) Request handling, CORS validation, route dispatch
│  app.py          │
└────────┬─────────┘
         │
         ▼
┌─────────────────────────┐
│ backend/                │ ── (4) Map 70 responses to 20 skills;
│ feature_extraction.py   │       normalize from [1, 5] Likert to [0.0, 10.0] scale
└────────┬────────────────┘
         │  [ 20-skill vector: { "Programming": 8.5, "Math": 9.0, ... } ]
         ▼
┌─────────────────────────┐
│ backend/                │ ── (5) Fuzzification (5 input sets) -> 420 Mamdani rules ->
│ fuzzy_engine.py         │       centroid defuzzification and matrix scoring -> 105 careers ranked
└────────┬────────────────┘
         │  [ Ranked compatibility scores 0–100% ]
         ▼
┌───────────────────────────┐
│ backend/                  │ ── (6) Select top 5 careers and generate match explanations
│ recommendation_engine.py  │
└────────┬──────────────────┘
         │
         ▼
┌───────────────────────────┐
│ backend/                  │ ── (7) Compare user scores against benchmark matrix:
│ skill_gap_analysis.py     │       Gap = Required - User Score
└────────┬──────────────────┘
         │
         ▼
┌───────────────────────────┐
│ backend/                  │ ── (8) Extract 6-step roadmap from roadmaps.csv;
│ roadmap_builder.py        │       mark steps targeting active skill gaps as priority
└────────┬──────────────────┘
         │
         ▼
┌───────────────────────────┐
│ backend/                  │ ── (9) Save session, raw responses, skill profile,
│ database.py               │       top5, top30, gaps, and roadmaps to careerlens.db
└────────┬────────────────┘
         │
         ▼  [ JSON payload returned to client ]
┌────────────────────────────────────────────────────────────────────────┐
│ Client-side visualization layer                                        │
├─────────────────────────┬────────────────────────┬─────────────────────┤
│ frontend/results.html   │ frontend/dashboard.html│ backend/app.py (PDF)│
│ • Top 5 career cards    │ • 20-skill radar chart │ • Downloadable      │
│ • Top 30 drawer table   │ • Top 5 bar chart      │   multi-page PDF    │
│ • Skill gap accordions  │ • Strengths & growth   │   report generated  │
│ • Roadmap checkboxes    │ • Historical attempts  │   with ReportLab    │
│ • 105-career explorer   │   and score deltas     │                     │
└─────────────────────────┴────────────────────────┴─────────────────────┘
```

---

## 3. Dataset files (`data/csv/`)
The core domain data lives in six structured CSV files inside `data/csv/`.

```
data/csv/
├── careers.csv                 (105 rows: master catalog and job metadata)
├── career_descriptions.csv    (105 rows: role definitions and toolsets)
├── career_skill_matrix.csv    (105 rows: benchmark requirements across 20 skills)
├── questions.csv               (70 rows: psychometric items across 5 modules)
├── roadmaps.csv                (630 rows: 6-stage roadmaps per career)
└── rules.csv                   (420 rows: 4 Mamdani fuzzy rules per career)
```

### 3.1 `careers.csv`
- Row count: 105 entries (+ 1 header row).
- Purpose: Master catalog of supported careers, storing salary ranges, market demand, difficulty ratings, and degree requirements.

| Column Name | Data Type | Description | Sample Value (Row 1) |
| :--- | :--- | :--- | :--- |
| `Career ID` | String (Alpha-Numeric) | Unique primary key identifier | `"AI001"` |
| `Career Name` | String | Standard job title | `"AI/ML Engineer"` |
| `Category` | String | Vocational field | `"Technology"` |
| `Description` | String | Summary of the role | `"Builds and trains machine learning models that let software learn from data."` |
| `Future Demand` | String (Enum) | Market demand rating (`High`, `Very High`, `Medium`) | `"Very High"` |
| `Avg Salary (LPA)` | Integer / String | Median Indian compensation in Lakhs Per Annum | `"12"` |
| `Difficulty` | String (Enum) | Entry difficulty (`Low`, `Medium`, `High`, `Very High`) | `"Very High"` |
| `Required Education`| String | Minimum degree requirement | `"B.Tech/B.E. (CS or related)"` |
| `Remote Work` | String (`Yes` / `No`) | Remote work feasibility | `"Yes"` |
| `Growth Rate` | String (Enum) | Sector expansion rate | `"High"` |
| `Industry` | String | Economic sector | `"IT/Software"` |

### 3.2 `career_descriptions.csv`
- Row count: 105 entries (+ 1 header row).
- Purpose: Contains day-to-day responsibilities, common software tools, representative hiring companies, and 5 to 10 year industry outlooks.

| Column Name | Data Type | Description | Sample Value (Row 1) |
| :--- | :--- | :--- | :--- |
| `Career` | String (FK to careers) | Matching career title | `"AI/ML Engineer"` |
| `Responsibilities`| String (Text) | Core operational tasks | `"Model building, data pipeline design, evaluation & tuning, deployment"` |
| `Tools` | String (Comma-Separated) | Frameworks and libraries | `"Python, TensorFlow, PyTorch, scikit-learn"` |
| `Companies` | String (Text) | Representative hiring organizations | `"Product-based tech firms, research labs, AI startups"` |
| `Future Scope` | String (Text) | 5 to 10 year industry outlook | `"Expanding demand driven by enterprise AI adoption across every industry"` |

### 3.3 `career_skill_matrix.csv`
- Row count: 105 entries (+ 1 header row).
- Purpose: Baseline benchmark skill levels on a 0 to 10 scale across all 20 skills.

| Column Name | Data Type | Description | Sample Value (Row 1: AI/ML Engineer) |
| :--- | :--- | :--- | :--- |
| `Career` | String | Career Name identifier | `"AI/ML Engineer"` |
| `Programming` | Float / Integer (0–10) | Software logic and coding | `10` |
| `Math` | Float / Integer (0–10) | Calculus, linear algebra, statistics | `10` |
| `Leadership` | Float / Integer (0–10) | Team guidance and coordination | `2` |
| `Communication`| Float / Integer (0–10) | Written and verbal clarity | `4` |
| `Problem Solving`| Float / Integer (0–10) | Analytical problem breakdown | `10` |
| `Business Thinking`| Float / Integer (0–10)| Commercial and operational context | `3` |
| `Creativity` | Float / Integer (0–10) | Divergent ideation | `6` |
| `Research Interest`| Float / Integer (0–10)| Literature review and experimentation | `8` |
| `Learning Ability`| Float / Integer (0–10)| Speed of picking up new topics | `9` |
| `Curiosity` | Float / Integer (0–10) | Inquisitiveness | `8` |
| `Discipline` | Float / Integer (0–10) | Work consistency and rigor | `7` |
| `Adaptability` | Float / Integer (0–10) | Flexibility with changing conditions | `5` |
| `Logical Thinking`| Float / Integer (0–10)| Deductive reasoning | `9` |
| `Decision Making`| Float / Integer (0–10)| Decision speed and clarity | `5` |
| `Innovation` | Float / Integer (0–10) | Developing novel approaches | `7` |
| `Empathy` | Float / Integer (0–10) | Understanding user or team perspectives | `2` |
| `Attention To Detail`| Float / Integer (0–10)| Precision and error checking | `7` |
| `Artistic Skill`| Float / Integer (0–10)| Visual craft and aesthetic design | `2` |
| `Physical Stamina`| Float / Integer (0–10)| Physical work endurance | `1` |
| `Teaching Ability`| Float / Integer (0–10)| Instruction and mentoring | `1` |

### 3.4 `questions.csv`
- Row count: 70 entries (+ 1 header row).
- Purpose: Psychometric survey questions presented in `assessment.html`, divided into 5 cognitive modules.

| Column Name | Data Type | Description | Sample Value (Row 1) |
| :--- | :--- | :--- | :--- |
| `Question ID` | String (`Q1` to `Q70`) | Unique question code | `"Q1"` |
| `Module` | String | Module name | `"M1 - Technical Skills"` |
| `Question` | String | Likert prompt text | `"I enjoy writing code to solve practical problems."` |
| `Mapped Skill` | String | Skill from the 20 master traits | `"Programming"` |

### 3.5 `roadmaps.csv`
- Row count: 630 entries (+ 1 header row), structured as 6 sequential steps for each of the 105 careers ($105 \times 6 = 630$).
- Purpose: Learning stages, targeted skills, estimated completion timelines, and resource recommendations.

| Column Name | Data Type | Description | Sample Value (Row 1) |
| :--- | :--- | :--- | :--- |
| `Career` | String | Career Name identifier | `"AI/ML Engineer"` |
| `Step Order` | Integer (1–6) | Stage sequence | `1` |
| `Step` | String (Text) | Practical learning objective | `"Master Python, NumPy, Pandas, Vectorized Linear Algebra and Multivariable Calculus"` |
| `Skill Targeted`| String | Main skill targeted in step | `"Math"` |
| `Estimated Duration`| String | Time needed | `"4-6 weeks"` |
| `Resource Type`| String | Recommended learning format | `"Interactive Math & Code Labs"` |
| `Milestone` | String (`Yes` / `No`) | Major milestone flag | `"No"` |

### 3.6 `rules.csv`
- Row count: 420 entries (+ 1 header row), structured as 4 rules for each of the 105 careers ($105 \times 4 = 420$).
- Purpose: Inference rule base evaluated by the fuzzy engine.

| Column Name | Data Type | Description | Sample Value (Row 1) |
| :--- | :--- | :--- | :--- |
| `Rule ID` | String (`R1` to `R420`) | Unique rule identifier | `"R1"` |
| `IF1_Skill` | String | First antecedent skill | `"Programming"` |
| `IF1_Level` | String (Linguistic) | Linguistic level (`Very Low`, `Low`, `Medium`, `High`, `Very High`) | `"Very High"` |
| `IF2_Skill` | String | Second antecedent skill | `"Math"` |
| `IF2_Level` | String (Linguistic) | Linguistic level | `"Very High"` |
| `IF3_Skill` | String | Third antecedent skill | `"Problem Solving"` |
| `IF3_Level` | String (Linguistic) | Linguistic level | `"Very High"` |
| `IF4_Skill` | String | Fourth antecedent skill | `"Learning Ability"` |
| `IF4_Level` | String (Linguistic) | Linguistic level | `"Very High"` |
| `THEN_Career` | String | Target career | `"AI/ML Engineer"` |
| `THEN_Level` | String (Linguistic) | Consequent level (`Low`, `Medium`, `High`, `Excellent`) | `"Excellent"` |

### 3.7 `data/userdata/` (User History & Attempt Exports)
The system maintains structured longitudinal datasets tracking student assessments and attempt progression:
- **`data/userdata/userdata.csv`**: Aggregated candidate records storing `user_id`, `unique_code`, `name`, `education`, `registered_at`, `total_attempts`, `completed_attempts`, `in_progress_attempts`, `last_attempt_id`, `last_attempt_date`, `last_attempt_status`, `latest_top_career`, `latest_compatibility_score`, `latest_top_3_careers`, `latest_top_5_careers`, and `all_assessment_ids`.
- **`data/userdata/user_attempts.csv`**: Granular attempt-by-attempt audit logs storing `assessment_id`, `user_id`, `unique_code`, `user_name`, `education`, `started_at`, `completed_at`, `status`, `responses_count`, and top career recommendations with compatibility scores.

---

## 4. Backend services (`backend/`)

```
backend/
├── app.py                   (REST API, route handlers, PDF export, CSV export routes)
├── database.py              (SQLite data access, schema, migration helpers)
├── userdata_exporter.py     (Real-time SQLite to CSV synchronization engine)
├── feature_extraction.py    (Likert score aggregation and 0–10 normalization)
├── fuzzy_engine.py          (Fuzzification, skfuzzy Mamdani engine, defuzzification)
├── recommendation_engine.py (Top-N ranking and explanation generation)
├── skill_gap_analysis.py    (Benchmark comparison and deficit calculation)
├── roadmap_builder.py       (Curriculum sequencing and priority flagging)
├── test_all_personas.py     (52-Persona multi-archetype system-wide stress test)
├── test_api_suite.py        (End-to-end API integration and PDF report test suite)
├── test_eval_integration.py (Evaluation benchmark integration test)
├── test_frontend_assets.py  (Frontend static asset and route integrity test)
└── test_pipeline.py         (Automated test suite across 5 archetypal profiles)
evaluation/
└── evaluate_recommendations.py (Information Retrieval ranking & benchmark metrics engine)
serve_frontend.py            (Multi-threaded standalone local preview server)
```

### 4.1 `backend/app.py`

#### Function signatures
```python
def _generate_code(name: str) -> str:
    """Generates an uppercase login code (such as ARJUN-4827)."""

def _err(msg: str, code: int = 400):
    """Formats a standardized JSON error response tuple."""

def register():
    """POST /api/register - Creates a user and returns user_id and unique_code."""

def login():
    """POST /api/login - Authenticates a user by code and returns profile with history."""

def save_draft():
    """POST /api/assessment/draft - Saves in-progress assessment draft responses."""

def get_draft(user_id: int):
    """GET /api/assessment/draft/<user_id> - Retrieves active draft responses for a user."""

def submit():
    """POST /api/submit - Runs full pipeline (feature extraction, fuzzy scoring, gaps, roadmaps) and saves to DB."""

def _hydrate_result(result: dict) -> dict:
    """Computes dynamic top30, all_scores, and fresh roadmaps in memory for read endpoints."""

def get_results(user_id: int):
    """GET /api/results/<user_id> - Fetches latest saved assessment results for a user."""

def get_history(user_id: int):
    """GET /api/user/<user_id>/history - Fetches chronological assessment history."""

def get_assessment_results(assessment_id: int):
    """GET /api/assessment/<assessment_id>/results - Fetches results of a specific assessment attempt."""

def get_careers():
    """GET /api/careers - Returns full 105-career catalog JSON from careers.csv."""

def generate_pdf_response(result: dict, user: dict, assessment_id: int):
    """Builds and streams a multi-page ReportLab PDF document."""

def generate_pdf(user_id: int):
    """GET /api/pdf/<user_id> - Downloads latest assessment PDF report."""

def generate_pdf_by_assessment(assessment_id: int):
    """GET /api/pdf/assessment/<assessment_id> - Downloads PDF for a specific assessment attempt."""

def health():
    """GET /api/health - Returns API health status and database path."""
```

#### API request and response formats

##### 1. `POST /api/register`
- Request body:
  ```json
  {
    "name": "Arjun Sharma",
    "education": "B.Tech Computer Science"
  }
  ```
- Response (HTTP 201):
  ```json
  {
    "user_id": 17,
    "unique_code": "ARJUN-4827",
    "name": "Arjun Sharma"
  }
  ```

##### 2. `POST /api/login`
- Request body:
  ```json
  {
    "unique_code": "ARJUN-4827"
  }
  ```
- Response (HTTP 200):
  ```json
  {
    "user_id": 17,
    "name": "Arjun Sharma",
    "education": "B.Tech Computer Science",
    "unique_code": "ARJUN-4827",
    "history": [
      {
        "assessment_id": 14,
        "started_at": "2026-08-20T17:33:33.434038+00:00",
        "completed_at": "2026-08-20T17:33:33.453017+00:00",
        "status": "completed",
        "top_careers": ["AI/ML Engineer", "Data Engineer", "Mechanical Engineer"],
        "top_compatibility": 96.0
      }
    ]
  }
  ```

##### 3. `POST /api/assessment/draft`
- Request body:
  ```json
  {
    "user_id": 17,
    "answers": {
      "Q1": 5,
      "Q2": 4
    }
  }
  ```
- Response (HTTP 200):
  ```json
  {
    "status": "saved",
    "assessment_id": 16,
    "count": 2
  }
  ```

##### 4. `GET /api/assessment/draft/<int:user_id>`
- Response (HTTP 200):
  ```json
  {
    "draft": {
      "assessment_id": 16,
      "started_at": "2026-08-20T18:17:09.673432+00:00",
      "answers": { "Q1": 5, "Q2": 4 },
      "count": 2
    },
    "has_draft": true
  }
  ```

##### 5. `POST /api/submit`
- Request body:
  ```json
  {
    "user_id": 17,
    "answers": {
      "Q1": 5, "Q2": 4, "Q3": 5, "Q4": 3, "Q5": 5,
      "Q6": 4, "Q7": 2, "Q8": 4, "Q9": 5, "Q10": 4
    }
  }
  ```
- Response (HTTP 200):
  ```json
  {
    "assessment_id": 14,
    "skill_profile": {
      "Programming": 9.2,
      "Math": 8.8,
      "Logical Thinking": 9.0,
      "Problem Solving": 8.5
    },
    "top5": [
      {
        "career": "AI/ML Engineer",
        "compatibility": 96.0,
        "category": "Technology",
        "avg_salary_lpa": "12",
        "future_demand": "Very High",
        "explanation": "Recommended because: Programming, Math, Problem Solving, and Logical Thinking.",
        "skill_gaps": [
          { "skill": "Research Interest", "user_score": 5.0, "required_score": 8.0, "gap": 3.0 }
        ],
        "roadmap": [
          {
            "step_order": 1,
            "step": "Master Python, NumPy, Vectorized Linear Algebra",
            "skill_targeted": "Math",
            "duration": "4-6 weeks",
            "resource_type": "Interactive Math & Code Labs",
            "milestone": false,
            "is_priority": false
          }
        ]
      }
    ],
    "top30": [
      { "career": "AI/ML Engineer", "compatibility": 96.0 },
      { "career": "Data Engineer", "compatibility": 58.4 }
    ],
    "all_scores": {
      "AI/ML Engineer": 96.0,
      "Data Engineer": 58.4
    },
    "skill_gaps": {
      "AI/ML Engineer": []
    },
    "roadmaps": {
      "AI/ML Engineer": []
    }
  }
  ```

---

### 4.2 `backend/database.py`

#### Function signatures
```python
class Database:
    def __init__(self, db_path: str = "careerlens.db"):
        """Initializes database path and sets up internal connection slot."""

    def connect(self) -> sqlite3.Connection:
        """Returns SQLite connection with row_factory=sqlite3.Row, foreign keys enabled, WAL mode, and normal sync."""

    def close(self):
        """Closes the current database connection if open."""

    def init_schema(self):
        """Runs table creation DDL and JSON column migrations."""

    def create_user(self, name: str, unique_code: str, education: str = None) -> int:
        """Inserts a new user record and returns the generated user_id."""

    def get_user_by_code(self, unique_code: str) -> Optional[dict]:
        """Looks up a user by their unique login code."""

    def get_user_by_id(self, user_id: int) -> Optional[dict]:
        """Looks up a user by integer user_id."""

    def start_assessment(self, user_id: int) -> int:
        """Inserts a new assessment row with status='in_progress' and returns assessment_id."""

    def complete_assessment(self, assessment_id: int):
        """Updates assessment status to 'completed' and records completion timestamp."""

    def save_responses(self, assessment_id: int, answers: Dict[str, int]):
        """Runs batch upsert for question-answer pairs."""

    def get_responses(self, assessment_id: int) -> Dict[str, int]:
        """Retrieves raw question-answer map for an assessment."""

    def save_draft(self, user_id: int, answers: Dict[str, int]) -> int:
        """Saves in-progress draft responses for an active assessment session."""

    def get_draft(self, user_id: int) -> Optional[dict]:
        """Retrieves active in-progress assessment responses for a user."""

    def _format_result_row(self, row: sqlite3.Row) -> dict:
        """Deserializes stored JSON fields into dictionaries."""

    def save_results(self, assessment_id: int, skill_profile: Dict[str, float], top5: List[dict], top30: Optional[List[dict]] = None, skill_gaps: Optional[dict] = None, roadmaps: Optional[dict] = None):
        """Saves or updates computed results in the database."""

    def get_results(self, assessment_id: int) -> Optional[dict]:
        """Fetches and deserializes results for a given assessment_id."""

    def get_latest_result(self, user_id: int) -> Optional[dict]:
        """Queries the user's latest assessment result ordered by ID descending."""

    def get_user_history(self, user_id: int) -> List[dict]:
        """Returns all completed and in-progress assessments for a user with match metadata."""
```

---

### 4.3 `backend/feature_extraction.py`

#### Function signatures
```python
def load_questions(csv_path: str) -> List[dict]:
    """Parses questions.csv and returns list of question items."""

def extract_features(answers: Dict[str, int], questions: List[dict]) -> Dict[str, float]:
    """Averages Likert 1-5 answers per mapped skill and normalizes to a 0.0-10.0 scale."""

def profile_completeness(answers: Dict[str, int], questions: List[dict]) -> float:
    """Calculates the ratio of answered questions to total questions (0.0 to 1.0)."""

def skill_confidence(questions: List[dict]) -> Dict[str, int]:
    """Counts the number of survey questions supporting each of the 20 skills."""
```

---

### 4.4 `backend/fuzzy_engine.py`

#### Function signatures
```python
class FuzzyEngine:
    def __init__(self, data_dir: str):
        """Loads rules.csv, careers.csv, and initializes control systems cache."""

    def _load_rules(self, path: Path) -> Dict[str, List[dict]]:
        """Parses rules.csv into antecedent and consequent mappings grouped by career."""

    def _load_careers(self, path: Path) -> List[str]:
        """Extracts list of all 105 career names from careers.csv."""

    def _make_skill_antecedent(self, name: str) -> ctrl.Antecedent:
        """Constructs a 0-10 input variable with 5 overlapping triangular membership functions."""

    def _make_compatibility_consequent(self) -> ctrl.Consequent:
        """Constructs a 0-100 output variable with 4 triangular membership functions."""

    def _build_system(self, career: str) -> ctrl.ControlSystemSimulation:
        """Constructs a skfuzzy ControlSystem for a career from its associated rules."""

    def _get_system(self, career: str) -> ctrl.ControlSystemSimulation:
        """Returns cached ControlSystemSimulation instance for a career."""

    def score_career(self, career: str, skill_profile: Dict[str, float]) -> float:
        """Runs Mamdani inference and centroid defuzzification for a single career."""

    def _skill_matrix_score(self, career: str, skill_profile: Dict[str, float]) -> float:
        """Computes fit score based on Pearson correlation, requirement deficits, and signature skills."""

    def load_skill_matrix(self, csv_path: str):
        """Loads benchmark requirements from career_skill_matrix.csv."""

    def score_all(self, skill_profile: Dict[str, float]) -> List[dict]:
        """Scores and ranks all 105 careers using fuzzy inference, matrix alignment, and rank decay."""
```

---

### 4.5 `backend/recommendation_engine.py`

#### Function signatures
```python
class RecommendationEngine:
    def __init__(self, data_dir: str):
        """Loads career_skill_matrix.csv and careers.csv metadata."""

    def _load_skill_matrix(self, path: Path) -> Dict[str, Dict[str, float]]:
        """Parses career_skill_matrix.csv into nested dictionaries."""

    def _load_career_meta(self, path: Path) -> Dict[str, dict]:
        """Loads category, description, salary, demand, and education metadata from careers.csv."""

    def _explain(self, career: str, skill_profile: Dict[str, float], max_reasons: int = 4) -> str:
        """Finds matching trait overlaps (user >= 6.5 and career >= 6.0) to generate match reasons."""

    def recommend(self, skill_profile: Dict[str, float], ranked_careers: List[dict], top_n: int = 5) -> List[dict]:
        """Attaches explanations, salary, demand, and education metadata to top ranked careers."""
```

---

### 4.6 `backend/skill_gap_analysis.py`

#### Function signatures
```python
class SkillGapAnalyzer:
    def __init__(self, data_dir: str):
        """Loads career_skill_matrix.csv benchmark requirements."""

    def _load_skill_matrix(self, path: Path) -> Dict[str, Dict[str, float]]:
        """Parses benchmark skill matrix CSV."""

    def analyze(self, career: str, skill_profile: Dict[str, float], top_n: int = None) -> List[dict]:
        """Calculates skill gaps (Required - User Score) sorted in descending order."""

    def analyze_for_recommendations(self, skill_profile: Dict[str, float], recommendations: List[dict], top_n_skills: int = 6) -> List[dict]:
        """Adds targeted skill gap tables to recommendation objects."""
```

---

### 4.7 `backend/roadmap_builder.py`

#### Function signatures
```python
class RoadmapBuilder:
    def __init__(self, data_dir: str):
        """Loads and sorts 6-step curricula from roadmaps.csv."""

    def _load_roadmaps(self, path: Path) -> Dict[str, List[dict]]:
        """Parses roadmaps.csv and ensures steps are ordered by step order ascending."""

    def build(self, career: str, skill_gaps: List[dict], top_gap_n: int = 5) -> List[dict]:
        """Builds 6-step roadmap and sets is_priority=True on steps addressing user skill deficits."""

    def build_for_recommendations(self, recommendations: List[dict], top_gap_n: int = 5) -> List[dict]:
        """Enriches recommendation objects with personalized roadmaps."""
```

---

### 4.8 `backend/test_pipeline.py`

#### Function signatures
```python
def generate_answers_for_profile(target_skills: Dict[str, float], questions: List[dict], default_score: float = 3.0) -> Dict[str, int]:
    """Generates synthetic 1-5 Likert answer dictionary that reproduces target 0-10 skill profile scores."""

def run_pipeline_tests() -> int:
    """Executes end-to-end assertions across all 5 test profiles and returns status code 0 on success."""
```

---

### 4.9 `backend/userdata_exporter.py`

#### Purpose
Maintains synchronized, exportable tabular CSV datasets (`data/userdata/userdata.csv` and `data/userdata/user_attempts.csv`) for student tracking, research, counselor review, and longitudinal analytics.

#### Function signatures
```python
def export_userdata_to_csv(db_path: Optional[str] = None) -> dict:
    """
    Reads users, assessments, responses, and results from SQLite
    and exports formatted CSV files to:
      - data/userdata/userdata.csv
      - data/userdata/user_attempts.csv
      - data/csv/userdata.csv
      - data/userdata.csv
    Returns dictionary with users_count, attempts_count, and exported file paths.
    """
```

#### Event triggers
- Account registration via `POST /api/register`
- In-progress assessment draft autosave via `POST /api/assessment/draft`
- Assessment completion via `POST /api/submit`
- Backend boot initialization and manual export via `GET /api/userdata/export`

---

## 5. Frontend interface (`frontend/`)

### 5.1 `frontend/index.html`
- Key JavaScript functions:
  - `updateLogo(theme)`: Switches logo asset between dark and light modes.
  - `setTheme(theme, persist)`: Updates DOM `data-theme` attribute and saves choice to storage.
  - `toggleTheme()`: Toggles active visual theme.
  - `initThree()`: Initializes WebGL renderer, perspective camera, lights, and 4,300 particle points.
  - `updateColors(theme)`: Updates Three.js material colors when switching themes.
  - `resize()`: Recalculates canvas dimensions and camera matrix on window resize.
  - `frame(t)`: RequestAnimationFrame render loop managing mouse aim easing, scroll position, and particle rotation.
- Storage keys used:
  - `localStorage.getItem("careerlens-theme")` / `localStorage.getItem("cl-theme")`: Reads saved theme.
  - `localStorage.setItem("careerlens-theme", theme)`: Persists theme choice.

---

### 5.2 `frontend/login.html`
- Key JavaScript functions:
  - `switchTab(tab)`: Toggles between registration and sign-in tabs.
  - `showMsg(id, text, type)`: Displays inline status or error messages.
  - `doRegister()`: Posts student registration to `/api/register` and shows generated code.
  - `copyCode()`: Copies generated login code to clipboard.
  - `doLogin()`: Posts unique code to `/api/login` and renders prior attempt history.
  - `goToDashboard()`: Navigates to `dashboard.html`.
  - `viewLastResult()`: Fetches user results and opens `results.html`.
  - `viewSpecificResult(assessmentId)`: Fetches a past historical attempt and opens `results.html`.
  - `goToAssessment()`: Navigates to `assessment.html` to start a new quiz.
- Storage keys used:
  - `sessionStorage.setItem("cl_user_id", data.user_id)`: Stores active user ID.
  - `sessionStorage.setItem("cl_user_name", data.name)`: Stores user name.
  - `sessionStorage.setItem("cl_user_code", code)`: Stores login code.
  - `sessionStorage.setItem("cl_results", JSON.stringify(data))`: Caches current results payload.
  - `localStorage.setItem("cl_pending_code", code)`: Saves login code across reloads.

---

### 5.3 `frontend/assessment.html`
- Key JavaScript functions:
  - `isModuleComplete(moduleIdx)`: Checks whether all questions in the current module are answered.
  - `countAnsweredInModule(moduleIdx)`: Counts answered items in the current module.
  - `countAnsweredOverall()`: Counts total answered questions out of 70.
  - `renderModule(moduleIdx)`: Renders module questions, Likert option buttons, and progress state.
  - `handleAnswer(globalIdx, val)`: Updates answer array, updates progress bar, and plays feedback audio.
  - `goToPrevModule()` / `goToNextModule()`: Steps through the 5 modules with slide transitions.
  - `launchMiniConfetti()`: Triggers celebration animation when finishing all questions.
  - `showScreen(id)`: Controls screen visibility (`screen-intro`, `screen-quiz`, `screen-done`).
  - `reportBtn.addEventListener("click", ...)`: Submits answer map to `/api/submit`.
- Storage keys used:
  - `sessionStorage.getItem("cl_user_id")`: Reads user ID for submit payload.
  - `sessionStorage.setItem("cl_assessment_done", "true")`: Flags quiz completion.
  - `sessionStorage.setItem("cl_saved_answers", JSON.stringify(answers))`: Persists in-progress selections.
  - `sessionStorage.setItem("cl_results", JSON.stringify(data))`: Caches computed results.

---

### 5.4 `frontend/results.html`
- Key JavaScript functions:
  - `renderHistoryBar(history, activeId, data)`: Renders attempt selector dropdown and status badges.
  - `renderMainContent(profile, top5, top30)`: Renders top 5 career cards, top 30 drawer, and 20-skill scores.
  - `renderSkillGaps(top5, skill_gaps)`: Builds interactive gap accordions with priority tags.
  - `renderRoadmaps(top5, roadmaps)`: Renders 6-stage roadmap timelines with milestone checkboxes and progress bars ($X/6$ steps).
  - `exportRoadmapMarkdown(careerName)`: Generates and downloads a Markdown (`.md`) checklist file for Notion or Obsidian.
  - `toggleStepComplete(career, stepNum, checked)`: Saves roadmap step completion state to `localStorage`.
  - `isStepDone(career, stepNum)`: Checks local storage for step completion.
  - `initSkillSimulation(profile, top5)`: Initializes what-if skill sliders (0.0 to 10.0) that recalibrate compatibility scores in real time.
  - `onSimSliderInput(skillName, value)`: Updates score shifts and renders delta badges (such as $+24\%$).
  - `resetSkillSimulation()`: Resets simulation sliders back to assessment baselines.
  - `toggleCareerComparison(careerName)`: Adds or removes a career from comparison dock (up to 2).
  - `openCareerComparisonModal()` / `closeCareerComparisonModal()`: Opens or closes the side-by-side comparison modal.
  - `clearCareerComparison()`: Clears selected careers and hides comparison dock.
  - `renderEvolutionSection(history)`: Builds attempt-over-attempt score change comparison tables.
  - `updateEvolutionComparison(pId, bId)`: Calculates score shifts between two assessment attempts.
  - `loadAssessmentById(assessmentId)`: Loads a specific past assessment attempt.
  - `loadLatestReport()`: Switches view back to newest assessment attempt.
  - `filterExplorer()` / `renderExplorerCards(list)`: Filters 105-career catalog by search term, industry, difficulty, or salary.
  - `downloadPdfReport()`: Opens `/api/pdf/<user_id>` in a new tab for download.
  - `initResultsPage()`: Sets up page lifecycle with an initialization guard (`isPageInitialized`).
- Storage keys used:
  - `sessionStorage.getItem("cl_results")`: Reads cached assessment results.
  - `sessionStorage.getItem("cl_user_id")`: Reads user ID to fetch results from backend.
  - `sessionStorage.setItem("cl_results", JSON.stringify(parsed))`: Updates cached results with fresh API data.
  - `localStorage.getItem("cl_rm_<career>_step_<num>")` / `setItem(...)`: Persists roadmap checkbox states.

---

### 5.5 `frontend/dashboard.html`
- Key JavaScript functions:
  - `renderRadarChart(skillProfile)`: Initializes 20-skill Chart.js radar chart.
  - `renderBarChart(top5)`: Initializes top 5 career compatibility horizontal bar chart.
  - `updateChartsTheme(theme)`: Updates chart grid and text colors when switching theme.
  - `renderStrengthsWeaknesses(skillProfile)`: Identifies top 3 strengths and top 3 growth opportunities.
  - `renderHistory(historyList)`: Builds chronological assessment attempt history cards.
  - `copyUserCode()`: Copies user code from header to clipboard.
  - `signOut()`: Clears user session storage and redirects to `login.html`.
  - `loadDashboard()`: Coordinates data fetching from `/api/results/<id>` and `/api/user/<id>/history`.
- Storage keys used:
  - `sessionStorage.getItem("cl_user_id")` / `sessionStorage.getItem("cl_user_code")`: Reads authentication tokens.
  - `sessionStorage.removeItem(...)` / `localStorage.removeItem(...)`: Clears stored keys on sign-out.

---

### 5.6 Frontend configuration and API client
- `frontend/js/config.js`:
  - Sets `window.CAREERLENS_CONFIG = { API_BASE: "http://localhost:5000/api", ... }` as the single base URL configuration for API calls.
- `frontend/js/api.js` (`CareerAPI`):
  - `submitAnswers(answers)`: Sends `POST /api/submit`.
  - `saveDraft(answers)`: Sends `POST /api/assessment/draft`.
  - `getDraft(userId)`: Sends `GET /api/assessment/draft/<userId>`.
  - `getResults(userId)`: Sends `GET /api/results/<userId>`.
  - `getUserHistory(userId)`: Sends `GET /api/user/<userId>/history`.
  - `getAssessmentResults(assessmentId)`: Sends `GET /api/assessment/<assessmentId>/results`.
  - `getCareers()`: Sends `GET /api/careers`.

---

## 6. Fuzzy inference engine

### 6.1 Membership functions and fuzzification
Fuzzification maps a numerical input ($x \in [0, 10]$) to linguistic truth values ($\mu \in [0, 1]$).

In CareerLens, each of the 20 input skills maps into 5 overlapping linguistic sets:

$$\mathcal{L}_{\text{input}} = \{\text{Very Low}, \text{Low}, \text{Medium}, \text{High}, \text{Very High}\}$$

Each set uses a standard triangular membership function $\mu_A(x) = \text{trimf}(x; [a, b, c])$:

$$\mu_A(x) = \begin{cases} 
0 & x \le a \\
\frac{x - a}{b - a} & a < x \le b \\
\frac{c - x}{c - b} & b < x < c \\
0 & x \ge c 
\end{cases}$$

```
Membership (μ)
  1.0 ▲   Very Low       Low         Medium        High       Very High
      │   \     /     \     /     \     /     \     /     \     /
      │    \   /       \   /       \   /       \   /       \   /
  0.5 │     \ /         \ /         \ /         \ /         \ /
      │      ╳           ╳           ╳           ╳           ╳
      │     / \         / \         / \         / \         / \
  0.0 └───┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴───► Skill Score (x)
         0.0   1.25  2.5   3.75  5.0   6.25  7.5   8.75  10.0
```

#### Input membership parameters ($x \in [0, 10]$):
- Very Low: $[0.0, 0.0, 2.5]$
- Low: $[0.0, 2.5, 5.0]$
- Medium: $[2.5, 5.0, 7.5]$
- High: $[5.0, 7.5, 10.0]$
- Very High: $[7.5, 10.0, 10.0]$

#### Output membership parameters ($y \in [0, 100]$ career compatibility):
- Low: $[0, 0, 40]$
- Medium: $[20, 45, 70]$
- High: $[50, 70, 90]$
- Excellent: $[75, 100, 100]$

---

### 6.2 Step-by-step numerical example

Consider a user profile with scores of $x = 7.5$ in Programming and $x = 8.0$ in Math.

#### Step 1: Input fuzzification
Evaluating $x = 7.5$ for Programming:
- $\mu_{\text{Very Low}}(7.5) = 0.0$ ($7.5 \ge 2.5$)
- $\mu_{\text{Low}}(7.5) = 0.0$ ($7.5 \ge 5.0$)
- $\mu_{\text{Medium}}(7.5) = \frac{7.5 - 7.5}{7.5 - 5.0} = 0.0$
- $\mu_{\text{High}}(7.5) = \text{trimf}(7.5; [5.0, 7.5, 10.0]) = \frac{7.5 - 5.0}{7.5 - 5.0} = 1.0$
- $\mu_{\text{Very High}}(7.5) = \text{trimf}(7.5; [7.5, 10.0, 10.0]) = \frac{7.5 - 7.5}{10.0 - 7.5} = 0.0$

Evaluating $x = 8.0$ for Math:
- $\mu_{\text{Medium}}(8.0) = 0.0$
- $\mu_{\text{High}}(8.0) = \text{trimf}(8.0; [5.0, 7.5, 10.0]) = \frac{10.0 - 8.0}{10.0 - 7.5} = \frac{2.0}{2.5} = 0.80$
- $\mu_{\text{Very High}}(8.0) = \text{trimf}(8.0; [7.5, 10.0, 10.0]) = \frac{8.0 - 7.5}{10.0 - 7.5} = \frac{0.5}{2.5} = 0.20$

Sum of memberships: $\mu_{\text{High}}(8.0) + \mu_{\text{Very High}}(8.0) = 0.80 + 0.20 = 1.00$.

#### Step 2: Rule firing strength evaluation
Evaluating two active rules for `AI/ML Engineer`:
- Rule 1: $\text{IF Programming is High } (\mu = 1.0) \text{ AND Math is High } (\mu = 0.80) \text{ THEN Compatibility is High}$
  $$\alpha_1 = \min(\mu_{\text{High}}(\text{Prog}), \mu_{\text{High}}(\text{Math})) = \min(1.0, 0.80) = 0.80$$

- Rule 2: $\text{IF Programming is High } (\mu = 1.0) \text{ AND Math is Very High } (\mu = 0.20) \text{ THEN Compatibility is Excellent}$
  $$\alpha_2 = \min(\mu_{\text{High}}(\text{Prog}), \mu_{\text{Very High}}(\text{Math})) = \min(1.0, 0.20) = 0.20$$

#### Step 3: Consequent implication and aggregation
- For Rule 1, clip the fuzzy set $\text{High} = [50, 70, 90]$ at height $\alpha_1 = 0.80$:
  $$\mu_{B'_1}(y) = \min(0.80, \mu_{\text{High}}(y))$$
- For Rule 2, clip the fuzzy set $\text{Excellent} = [75, 100, 100]$ at height $\alpha_2 = 0.20$:
  $$\mu_{B'_2}(y) = \min(0.20, \mu_{\text{Excellent}}(y))$$

Combine using standard fuzzy maximum:
$$\mu_{\text{agg}}(y) = \max \left( \mu_{B'_1}(y), \mu_{B'_2}(y) \right)$$

```
Aggregated output area μ_agg(y)
  1.0 ▲
      │            Rule 1 (Clipped at 0.80)
  0.8 │          ┌──────────┐
      │         /            \
  0.5 │        /              \         Rule 2 (Clipped at 0.20)
  0.2 │       /                \───────┌─────────┐
      │      /                         │         │
  0.0 └─────┴────────────┴─────────────┴─────────┴──────► Compatibility (y%)
            50           70            90       100
```

#### Step 4: Centroid defuzzification
Calculate the center of gravity of the aggregated region:

$$y^* = \frac{\int_{0}^{100} y \cdot \mu_{\text{agg}}(y) \, dy}{\int_{0}^{100} \mu_{\text{agg}}(y) \, dy} \approx 72.4\%$$

This raw fuzzy score ($72.4\%$) is then combined with the career skill matrix correlation and penalty adjustments to produce the final ranked output.

---

## 7. Results and validation

The recommendation pipeline was tested with `backend/test_pipeline.py`. The suite validates 5 archetypal student profiles against all 105 careers.

```
========================================================================
  CareerLens Automated Pipeline Validation Suite Summary
========================================================================
  Total Archetypal Profiles Tested : 5
  Passed                           : 5
  Failed                           : 0
  Validation Rate                  : 100.0%
========================================================================
```

### 7.1 Test profile outcomes

| Test # | Profile Name | Key Target Highlight Skills (Scale 0–10) | Top Matched Career | Top Compatibility Score | Category / Domain | Validated Status |
| :---: | :--- | :--- | :--- | :---: | :--- | :---: |
| #1 | Strong Programmer | `Programming: 9.0`, `Math: 9.0`, `Problem Solving: 9.0`, `Learning Ability: 8.0` | AI/ML Engineer | 96.0% | Technology | PASS |
| #2 | Creative Designer | `Creativity: 9.0`, `Artistic Skill: 9.0`, `Communication: 8.0`, `Empathy: 7.0` | Content Strategist | 96.0% | Marketing / Creative | PASS |
| #3 | Strong Communicator / Leader | `Communication: 9.0`, `Leadership: 9.0`, `Empathy: 8.0`, `Business Thinking: 8.0` | Business Analyst | 96.0% | Business / Management | PASS |
| #4 | Security Analyst | `Logical Thinking: 9.0`, `Attention To Detail: 9.0`, `Problem Solving: 8.0`, `Programming: 7.0` | Cloud Engineer | 96.0% | Technology | PASS |
| #5 | All-Medium Baseline | All 20 Skills = `5.0 / 10.0` (Balanced Profile) | AI/ML Engineer | 48.7% | Technology (Baseline) | PASS |

### 7.2 Detailed rankings per profile

#### Profile 1: Strong Programmer
1. AI/ML Engineer: 96.0% (Technology, 12 LPA)
2. Data Engineer: 58.4% (Technology, 10 LPA)
3. Mechanical Engineer: 57.2% (Engineering, 5 LPA)
4. Backend Developer: 56.0% (Technology, 9 LPA)
5. Data Analyst: 54.8% (Technology, 6 LPA)

#### Profile 2: Creative Designer
1. Content Strategist: 96.0% (Marketing, 6 LPA)
2. Psychologist / Counselor: 94.7% (Healthcare, 6 LPA)
3. Graphic Designer: 93.5% (Design, 4 LPA)
4. Fashion Designer: 92.3% (Design, 5 LPA)
5. Customer Success Manager: 91.1% (Business, 9 LPA)

#### Profile 3: Strong Communicator / Leader
1. Business Analyst: 96.0% (Business, 7 LPA)
2. Digital Marketing Specialist: 94.7% (Marketing, 6 LPA)
3. HR Manager: 93.5% (Management, 7 LPA)
4. Entrepreneur / Founder: 92.3% (Business, Flexible)
5. Psychologist / Counselor: 91.1% (Healthcare, 6 LPA)

#### Profile 4: Security Analyst
1. Cloud Engineer: 96.0% (Technology, 10 LPA)
2. Frontend Developer: 94.7% (Technology, 8 LPA)
3. QA Automation Engineer: 93.5% (Technology, 7 LPA)
4. MLOps Engineer: 92.3% (Technology, 14 LPA)
5. Security Engineer: 91.1% (Technology, 12 LPA)

#### Profile 5: All-Medium Baseline Profile
1. AI/ML Engineer: 48.7%
2. Data Scientist: 47.4%
3. Cybersecurity Analyst: 46.2%
4. UI/UX Designer: 45.0%
5. Software Engineer: 43.8%

---

## 8. Limitations and future work

### 8.1 Current limitations
1. Self-report bias: Likert scale surveys rely on self-assessment, which can lead to overestimation or underestimation of actual competency depending on individual calibration.
2. Static rule matrices: The 420 rules and 105 career benchmark vectors reflect fixed domain benchmarks. Emerging hybrid roles require manual updates to the CSV tables.
3. Offline compensation data: Salaries, demand ratings, and growth projections are stored statically in CSVs rather than synchronized with live job market feeds.

### 8.2 Planned improvements

1. Adaptive Neuro-Fuzzy Inference (ANFIS):
Use hybrid gradient descent and least-squares optimization to automatically calibrate triangular membership parameters and rule weights based on real student outcome datasets.

2. Live labor market API integration:
Connect CareerLens directly to programmatic job data sources (such as the Adzuna API or O*NET Web Services) to update salary figures, hiring demand, and skill requirements in real time.

3. Objective skill testing modules:
Add practical micro-tasks (such as small code challenges, logic puzzles, and layout tests) alongside Likert questions to establish calibrated baseline proficiency scores.

4. Retrieval-Augmented Generation (RAG) career assistant:
Integrate a localized language model loaded with the student's 20-skill scores, active deficits, and roadmap milestones to answer specific questions, conduct mock interview practice, and recommend projects.

5. Resume and portfolio parsing:
Add automated PDF/DOCX resume ingestion and GitHub profile analysis to detect demonstrated tools and project experience, pre-populating baseline skill scores.

6. LMS and credential synchronization:
Support course verification protocols and learning platform APIs (such as Coursera, edX, or OpenBadges) to automatically mark roadmap milestone steps as completed.

---

## 9. Conclusion
CareerLens uses fuzzy set theory and Mamdani inference to provide granular, interpretable career guidance. By replacing rigid categorization with continuous membership modeling, benchmark gap quantification, and sequenced roadmaps, the platform offers an explainable and reliable foundation for career planning.

---

## 10. Database schema

CareerLens uses an embedded SQLite database (`careerlens.db`) with foreign key constraints and WAL mode enabled.

### 10.1 SQL DDL schema

```sql
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    unique_code TEXT    UNIQUE NOT NULL,
    education   TEXT,
    created_at  TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS assessments (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL,
    started_at   TEXT    NOT NULL,
    completed_at TEXT,
    status       TEXT    NOT NULL DEFAULT 'in_progress',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS responses (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id  INTEGER NOT NULL,
    question_id    TEXT    NOT NULL,
    answer_value   INTEGER NOT NULL,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE,
    UNIQUE (assessment_id, question_id)
);

CREATE TABLE IF NOT EXISTS results (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id       INTEGER NOT NULL UNIQUE,
    skill_profile_json  TEXT    NOT NULL,
    top5_json           TEXT    NOT NULL,
    top30_json          TEXT,
    skill_gaps_json     TEXT,
    roadmaps_json       TEXT,
    created_at          TEXT    NOT NULL,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE
);
```

### 10.2 Table structure and relationships

```
┌──────────────┐          1:N          ┌──────────────────┐
│    users     │ ────────────────────< │   assessments    │
└──────────────┘                       └────────┬─────────┘
                                                │
                                  1:N ┌─────────┴─────────┐ 1:1
                                      │                   │
                                      ▼                   ▼
                               ┌──────────────┐   ┌──────────────┐
                               │  responses   │   │   results    │
                               └──────────────┘   └──────────────┘
```

1. `users` table: Stores student identity records. Each student receives an alphanumeric code (`unique_code`, such as `ARJUN-4827`) for passwordless login.
2. `assessments` table: Tracks assessment sessions. Maintains a 1-to-many relationship with `users` (`user_id` foreign key) and tracks session status (`in_progress` or `completed`) with ISO timestamps.
3. `responses` table: Stores discrete Likert response items (1 to 5) for each question. Uses a unique constraint on `(assessment_id, question_id)` to allow idempotent upserts.
4. `results` table: Stores computed analysis serialized as JSON strings (`skill_profile_json`, `top5_json`, `top30_json`, `skill_gaps_json`, `roadmaps_json`). Maintains a 1-to-1 relationship with `assessments` (`assessment_id` unique foreign key).

---

## 11. API reference

| HTTP Method | API Endpoint | Description | Request Body | Response Format |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/register` | Registers a new student account and returns user identity with a generated login code. | `{"name": "string", "education": "string"}` | `{"user_id": int, "unique_code": "string", "name": "string"}` (HTTP 201) |
| `POST` | `/api/login` | Authenticates existing student by unique login code and returns user profile with attempt history. | `{"unique_code": "string"}` | `{"user_id": int, "name": "string", "education": "string", "unique_code": "string", "history": [...]}` (HTTP 200) |
| `POST` | `/api/assessment/draft` | Auto-saves in-progress assessment draft responses. | `{"user_id": int, "answers": {"Q1": 5, ...}}` | `{"status": "saved", "assessment_id": int, "count": int}` (HTTP 200) |
| `GET` | `/api/assessment/draft/<int:user_id>` | Retrieves in-progress assessment draft responses for a user if present. | None | `{"draft": {"assessment_id": int, "started_at": "string", "answers": {...}, "count": int}, "has_draft": bool}` (HTTP 200) |
| `POST` | `/api/submit` | Submits assessment answers, runs feature extraction, fuzzy inference, gap analysis, roadmap assembly, and saves results. | `{"user_id": int, "answers": {"Q1": 5, ...}}` | `{"assessment_id": int, "skill_profile": {...}, "top5": [...], "top30": [...], "all_scores": {...}, "skill_gaps": {...}, "roadmaps": {...}}` (HTTP 200) |
| `GET` | `/api/results/<int:user_id>` | Retrieves the most recent assessment result for a given user. | None | `{"assessment_id": int, "skill_profile": {...}, "top5": [...], "top30": [...], "all_scores": {...}, "skill_gaps": {...}, "roadmaps": {...}}` (HTTP 200) |
| `GET` | `/api/assessment/<int:assessment_id>/results` | Retrieves the results of a specific assessment attempt by assessment ID. | None | `{"assessment_id": int, "skill_profile": {...}, "top5": [...], "top30": [...], "all_scores": {...}, "skill_gaps": {...}, "roadmaps": {...}}` (HTTP 200) |
| `GET` | `/api/user/<int:user_id>/history` | Fetches chronological assessment history for a user with status and top matches. | None | `[{"assessment_id": int, "started_at": "string", "completed_at": "string", "status": "string", "top_careers": [...], "top_compatibility": float}]` (HTTP 200) |
| `GET` | `/api/careers` | Returns the complete 105-career catalog with salary, demand, category, and educational prerequisites. | None | `[{"career_id": "string", "career": "string", "category": "string", "avg_salary_lpa": "string", "future_demand": "string", ...}]` (HTTP 200) |
| `GET` | `/api/pdf/<int:user_id>` | Streams a downloadable ReportLab PDF summary report for the user's latest assessment. | None | Binary PDF Stream (`Content-Type: application/pdf`, `Content-Disposition: attachment`) |
| `GET` | `/api/pdf/assessment/<int:assessment_id>` | Streams a downloadable ReportLab PDF summary report for a specific assessment attempt. | None | Binary PDF Stream (`Content-Type: application/pdf`, `Content-Disposition: attachment`) |
| `GET` | `/api/health` | Service health check probe returning server status and database path. | None | `{"status": "ok", "db": "string"}` (HTTP 200) |

---

## 12. References

### 12.1 Academic literature
1. Zadeh, L. A. (1965). *Fuzzy Sets*. Information and Control, 8(3), 338–353.  
   DOI: [10.1016/S0019-9958(65)90241-X](https://doi.org/10.1016/S0019-9958(65)90241-X)  
   Foundational paper defining fuzzy set theory, continuous membership functions $\mu_A(x) \in [0, 1]$, and fuzzy set operations.
2. Mamdani, E. H., & Assilian, S. (1975). *An experiment in linguistic synthesis with a fuzzy logic controller*. International Journal of Man-Machine Studies, 7(1), 1–13.  
   DOI: [10.1016/S0020-7373(75)80002-2](https://doi.org/10.1016/S0020-7373(75)80002-2)  
   Introduces the Mamdani max-min compositional rule of inference used in the CareerLens recommendation engine.
3. Holland, J. L. (1997). *Making vocational choices: A theory of vocational personalities and work environments*. Psychological Assessment Resources.  
   Theoretical foundation for vocational typology and multi-trait interest classification.
4. Jang, J.-S. R. (1993). *ANFIS: Adaptive-Network-Based Fuzzy Inference System*. IEEE Transactions on Systems, Man, and Cybernetics, 23(3), 665–685.  
   DOI: [10.1109/21.256541](https://doi.org/10.1109/21.256541)  
   Reference architecture for neuro-fuzzy optimization loops.

### 12.2 Software libraries
1. Scikit-Fuzzy (Python Fuzzy Logic Toolbox)  
   Documentation: [https://pythonhosted.org/scikit-fuzzy/](https://pythonhosted.org/scikit-fuzzy/)  
   GitHub Repository: [https://github.com/scikit-fuzzy/scikit-fuzzy](https://github.com/scikit-fuzzy/scikit-fuzzy)
2. Flask Web Framework  
   Documentation: [https://flask.palletsprojects.com/en/stable/](https://flask.palletsprojects.com/en/stable/)
3. SQLite Write-Ahead Logging (WAL) Specification  
   Reference: [https://www.sqlite.org/wal.html](https://www.sqlite.org/wal.html)
4. ReportLab PDF Generation Library  
   User Guide: [https://www.reportlab.com/docs/reportlab-userguide.pdf](https://www.reportlab.com/docs/reportlab-userguide.pdf)
5. Chart.js Visualization Engine  
   Documentation: [https://www.chartjs.org/docs/latest/](https://www.chartjs.org/docs/latest/)
6. Three.js WebGL Library  
   Documentation: [https://threejs.org/docs/](https://threejs.org/docs/)

### 12.3 Occupational data sources
1. O*NET OnLine (U.S. Department of Labor / Employment and Training Administration)  
   Portal: [https://www.onetonline.org/](https://www.onetonline.org/)  
   Standardized occupational classification, ability ratings, and task requirement definitions.
2. National Career Service (Ministry of Labour and Employment, Government of India)  
   Portal: [https://www.ncs.gov.in/](https://www.ncs.gov.in/)  
   Indian employment sector classifications, skill benchmarks, and vocational roadmaps.
3. Adzuna Job Market API  
   Developer Portal: [https://developer.adzuna.com/](https://developer.adzuna.com/)
