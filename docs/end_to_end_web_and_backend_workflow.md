# CareerLens — Complete End-to-End Web & Backend Operational Workflow

---

## 📖 Executive Introduction

This document provides an exhaustive, step-by-step technical explanation of **how the entire CareerLens vocational platform operates from start to finish**.

It details:
- Every single web page and user interaction (clicks, toggles, form submissions, sliders, checkboxes).
- Exactly what JavaScript functions and HTTP requests are triggered on the frontend.
- Exactly how the Python Flask backend processes each request.
- The specific libraries, algorithms, mathematical formulas, and SQLite database queries executed behind the scenes.
- How assessment drafts, user history, CSV exports, and personalized roadmaps are managed in real-time.

---

## 🗺️ System Architecture & Lifecycle Map

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                               0. SERVER INITIALIZATION & BOOT                           │
│  python backend/app.py ──> SQLite WAL Mode ──> 6 CSV Datasets Loaded ──> Real-Time CSV Sync │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                             │
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                               1. LANDING PAGE (index.html)                              │
│  • Three.js 4,300 Particle Field  • Audio Engine  • Theme Toggle  • Stacking Context Nav │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                             │
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                         2. AUTHENTICATION HUB (login.html)                              │
│  • Register: Generates Unique Code (e.g. SHASH-6722) ──> Parameterized SQL ──> CSV Sync  │
│  • Login: Queries History & Previous Attempts via SQLite LEFT JOIN                      │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                             │
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                       3. 70-QUESTION ASSESSMENT (assessment.html)                       │
│  • Likert 1-5 Scale  • Real-Time Draft Autosave (/api/assessment/draft) ──> Draft Resumption│
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                             │ (Click "Submit Assessment")
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                      4. CORE ANALYTICAL BACKEND PIPELINE (/api/submit)                  │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐   │
│  │ 1. Likert -> [0, 10] Normalization (feature_extraction.py)                       │   │
│  │ 2. Mamdani Fuzzy Inference & Centroid Defuzzification (fuzzy_engine.py)          │   │
│  │ 3. Pearson Shape Correlation & Non-Linear Deficit Weighting (recommendation.py)  │   │
│  │ 4. Fit-Preserving Exponential Scaling (12% to 96%)                               │   │
│  │ 5. Skill Gap Analysis: Δ = Required - User Score (skill_gap_analysis.py)         │   │
│  │ 6. Milestone Curriculum Assembly & Priority Flagging (roadmap_builder.py)        │   │
│  │ 7. Atomic SQLite Persistence & Real-Time userdata.csv Exporter (userdata_export)│   │
│  └──────────────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                             │
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                          5. INTERACTIVE RESULTS HUB (results.html)                      │
│  • Top 5 Cards with Explanations • Top 30 Drawer • Interactive Roadmap Checkboxes       │
│  • "What-If?" 60fps Skill Simulation Lab • Side-by-Side Comparator • ReportLab PDF Export│
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                             │
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                     6. LONGITUDINAL DASHBOARD & EVALUATION (dashboard.html / eval)      │
│  • 20-Skill Radar Chart • Top 5 Bar Chart • Attempt Evolution • Model IR Benchmark Hub  │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ PHASE 0: Server Boot & System Initialization

When the developer or server executes `python backend/app.py`:

```bash
cd backend
python app.py
```

### 1. Python Environment & Library Ingestion
The Python interpreter loads key dependencies:
- **`Flask` & `Flask-CORS`**: Provides the HTTP routing engine and cross-origin resource sharing headers.
- **`sqlite3`**: The native C-based relational database engine.
- **`scikit-fuzzy` & `numpy`**: Vectorized numerical computation and Mamdani fuzzy membership evaluation.
- **`reportlab`**: Low-level PDF canvas layout and document compiler.
- **`pathlib` & `json` & `csv`**: High-performance filesystem and serialization utilities.

### 2. Database Schema Initialization & WAL Mode
`app.py` instantiates `Database("careerlens.db")` which executes `init_schema()` in `database.py`:
- **Write-Ahead Logging (WAL)**: Executes `PRAGMA journal_mode = WAL; PRAGMA synchronous = NORMAL; PRAGMA foreign_keys = ON;`. This ensures readers (fetching results, reading history) never block writers (saving drafts, submitting quizzes).
- **Tables Initialized**:
  - `users`: Stores candidate ID, full name, unique alphanumeric code, educational background, and registration timestamp.
  - `assessments`: Stores session ID, user reference, start timestamp, completion timestamp, and status (`in_progress` vs `completed`).
  - `responses`: Stores individual question responses (`Q1` to `Q70`, Likert ratings 1 to 5) with a composite unique index on `(assessment_id, question_id)` to support instant upserts.
  - `results`: Stores serialized JSON objects for `skill_profile_json`, `top5_json`, `top30_json`, `skill_gaps_json`, and `roadmaps_json`.

### 3. In-Memory Domain Knowledge Ingestion
The backend reads the 6 domain CSV datasets from `data/csv/` into high-speed memory structures:
- `questions.csv` $\to$ Parsed into 70 question dictionary items.
- `rules.csv` $\to$ Parsed into 420 Mamdani rule structures indexed by target career.
- `careers.csv` $\to$ Parsed into 105 career metadata records (salary, demand, industry, education).
- `career_skill_matrix.csv` $\to$ Stored as a $105 \times 20$ benchmark matrix.
- `roadmaps.csv` $\to$ Indexed into 630 sequential step milestones.

### 4. Real-Time CSV Exporter Cold-Start
The backend immediately invokes `export_userdata_to_csv()` from `backend/userdata_exporter.py`:
- Pulls all current database users and assessment sessions.
- Generates and synchronizes `data/userdata/userdata.csv` and `data/userdata/user_attempts.csv`.

---

## 🌐 PHASE 1: Landing Page (`index.html`)

The user opens `http://localhost:5000/` in their web browser.

### 1. Visual Rendering & 3D Particle Constellation
- **Three.js WebGL Engine**: `index.html` initializes a Three.js scene with a perspective camera and 4,300 particle points forming a mathematical attractor sculpture.
- **RequestAnimationFrame Loop**: The `frame(t)` function smoothly rotates the particle cloud and applies an easing vector toward the user's cursor coordinates.
- **Isolated CSS Stacking Context**:
  - The `<header>` navigation bar is wrapped in `.chrome` at `z-index: 100` with `backdrop-filter: blur(12px)` and `-webkit-backdrop-filter: blur(12px)`.
  - Main scene sections (`#one`, `#two`, `#three`) are layered at `z-index: 2`.
  - **Result**: When the user scrolls down, giant typographic headers smoothly slide *underneath* the frosted-glass navigation bar without visual overlap.

### 2. Interactive Buttons & Actions on `index.html`

#### A. Ambient Audio Music Player
- **Click Play / Pause Button (`#playPauseBtn`)**:
  - Calls `window.playPauseMusic()` in `js/music.js`.
  - Initiates HTML5 `Audio` playback using streaming tracks.
  - Synchronizes track state across all browser tabs via `localStorage.setItem("careerlens_music_playing", "true")`.
- **Click Prev / Next Track (`#prevTrackBtn`, `#nextTrackBtn`)**:
  - Cycles to the previous/next audio track in the playlist and updates the track title banner.
- **Click 3D Background Toggle (`#musicPlayer3dToggle`)**:
  - Calls `window.toggle3dBackground()`, toggling visibility of `#field` canvas to reduce GPU usage on lower-power devices.

#### B. Theme Toggle Button (`#themeToggle`)
- **Click Sun/Moon Toggle**:
  - Executes `toggleTheme()`.
  - Updates the root HTML attribute: `<html data-theme="dark">` or `<html data-theme="light">`.
  - Persists preference in `localStorage.setItem("careerlens-theme", theme)`.
  - Dispatches color update to Three.js particles (switching between warm rust `#B5502E` and void black `#171512`).

#### C. Navigation Links
- **Click "System Score ↗"**: Navigates to `/evaluation` (the Evaluation & Benchmark Dashboard).
- **Click "Begin Assessment ↗" / Hero CTA**: Navigates to `login.html`.

---

## 🔐 PHASE 2: Authentication & Registration Hub (`login.html`)

The user arrives at `login.html`. The page offers two distinct workflows:

```
┌─────────────────────────────────────────────────────────────┐
│                    DUAL AUTHENTICATION HUB                  │
├──────────────────────────────┬──────────────────────────────┤
│  TAB 1: NEW CANDIDATE        │  TAB 2: RETURNING CANDIDATE  │
│  • Enter Full Name           │  • Enter 9-Char Login Code   │
│  • Enter Degree / Branch     │    (e.g. SHASH-6722)         │
│  • [CREATE ACCOUNT & START]  │  • [SIGN IN & CONTINUE]      │
└──────────────────────────────┴──────────────────────────────┘
```

### 1. Workflow A: New Candidate Registration

#### What happens on the Frontend:
1. User enters their Name (e.g. `"Priya Patel"`) and Education (e.g. `"B.Tech Computer Science"`).
2. User clicks **"CREATE ACCOUNT & START ↗"**.
3. JavaScript in `login.html` intercepts the submit event, validates inputs, and triggers:
   ```javascript
   const res = await fetch("/api/register", {
     method: "POST",
     headers: { "Content-Type": "application/json" },
     body: JSON.stringify({ name: "Priya Patel", education: "B.Tech Computer Science" })
   });
   ```

#### What happens on the Backend (`app.py -> register()`):
1. **Validation**: Checks `name` is not empty.
2. **Code Generation (`_generate_code`)**:
   - Takes the first 5 alphabetic characters of the name in uppercase (`"PRIYA"`).
   - Generates 4 pseudo-random digits using `random.choices(string.digits, k=4)` (e.g. `"8283"`).
   - Joins them: `"PRIYA-8283"`.
   - Executes `SELECT id FROM users WHERE unique_code = 'PRIYA-8283'` in SQLite to guarantee uniqueness.
3. **Database Insertion (`db.create_user`)**:
   - Executes parameterized prepared statement:
     ```sql
     INSERT INTO users (name, unique_code, education, created_at)
     VALUES ('Priya Patel', 'PRIYA-8283', 'B.Tech Computer Science', '2026-08-28T16:07:26Z');
     ```
   - SQLite returns newly generated auto-incrementing integer `user_id = 37`.
4. **Real-Time CSV Export Trigger**:
   - Invokes `export_userdata_to_csv()`.
   - Appends the new user record into `data/userdata/userdata.csv` with `total_attempts = 0` and status `no_attempts`.
5. **HTTP Response**:
   - Returns HTTP 201 JSON payload:
     ```json
     { "user_id": 37, "unique_code": "PRIYA-8283", "name": "Priya Patel" }
     ```

#### Frontend Completion:
- Stores session in `sessionStorage.setItem("careerlens_user", JSON.stringify(data))`.
- Displays modal showcasing the candidate's unique code with a "Copy to Clipboard" button.
- Automatically redirects the browser to `assessment.html`.

---

### 2. Workflow B: Returning Candidate Login

#### What happens on the Frontend:
1. User enters their unique 9-character code (e.g. `"PRIYA-8283"`).
2. User clicks **"SIGN IN & CONTINUE ↗"**.
3. JavaScript sends:
   ```javascript
   const res = await fetch("/api/login", {
     method: "POST",
     headers: { "Content-Type": "application/json" },
     body: JSON.stringify({ unique_code: "PRIYA-8283" })
   });
   ```

#### What happens on the Backend (`app.py -> login()`):
1. **User Query**: Queries `SELECT * FROM users WHERE unique_code = ?`.
2. **History Retrieval (`db.get_user_history`)**:
   - Executes SQL query joining `assessments` and `results`:
     ```sql
     SELECT a.id as assessment_id, a.started_at, a.completed_at, a.status,
            r.created_at as result_created_at, r.top5_json
     FROM assessments a
     LEFT JOIN results r ON r.assessment_id = a.id
     WHERE a.user_id = 37
     ORDER BY a.id DESC;
     ```
   - For each historical assessment, deserializes `top5_json` to extract top 3 careers and highest match score.
3. **HTTP Response**:
   - Returns user profile and history array:
     ```json
     {
       "user_id": 37,
       "name": "Priya Patel",
       "education": "B.Tech Computer Science",
       "unique_code": "PRIYA-8283",
       "history": [
         {
           "assessment_id": 37,
           "status": "completed",
           "top_careers": ["Embedded Systems Engineer", "Data Analyst", "Blockchain Developer"],
           "top_compatibility": 96.0,
           "completed_at": "2026-08-28T16:07:26Z"
         }
       ]
     }
     ```

#### Frontend Completion:
- Populates past assessment history cards with direct links to view previous reports.
- Stores user in `sessionStorage` and navigates to `dashboard.html` (if completed) or `assessment.html` (to start/resume a quiz).

---

## 📝 PHASE 3: 70-Question Diagnostic Assessment (`assessment.html`)

The candidate begins the 70-statement psychometric evaluation.

### 1. Assessment Structure & Categorization
The 70 statements from `questions.csv` are divided across 5 cognitive modules:
- **Module 1: Technical Aptitude** (Programming, Math, Logical Thinking, Problem Solving).
- **Module 2: Creative & Design Skills** (Creativity, Artistic Skill, Innovation).
- **Module 3: Business & Strategic Leadership** (Leadership, Communication, Business Thinking, Decision Making).
- **Module 4: Research, Science & Learning** (Research Interest, Learning Ability, Curiosity, Attention to Detail).
- **Module 5: Behavioral, Social & Physical Traits** (Discipline, Adaptability, Empathy, Physical Stamina, Teaching Ability).

Each statement uses a 5-point Likert scale:
`1 = Strongly Disagree` | `2 = Disagree` | `3 = Neutral` | `4 = Agree` | `5 = Strongly Agree`.

---

### 2. Real-Time Draft Autosave Architecture

To protect candidates from network drops or accidental browser closes, CareerLens features real-time autosaving:

#### A. Initial Draft Check on Page Load:
- Frontend sends `GET /api/assessment/draft/<user_id>`.
- Backend queries `SELECT id, started_at FROM assessments WHERE user_id = ? AND status = 'in_progress'`.
- If an unfinished draft exists, backend fetches responses via `SELECT question_id, answer_value FROM responses WHERE assessment_id = ?`.
- Frontend automatically pre-populates all answered radio buttons, jumps the candidate directly to their last answered question, and displays an animated pill: **"Draft Restored"**.

#### B. Continuous Background Autosave on Every Answer:
- Whenever the user clicks any Likert radio button (1–5) or clicks "Next":
  1. Frontend captures the answer in memory: `state.answers["Q1"] = 4`.
  2. Debounced API call fires: `POST /api/assessment/draft` with `{ "user_id": 37, "answers": state.answers }`.
  3. Backend executes `db.save_draft(user_id, answers)`:
     - Gets or creates an `in_progress` record in `assessments`.
     - Executes SQLite `executemany()` batch upsert:
       ```sql
       INSERT INTO responses (assessment_id, question_id, answer_value)
       VALUES (?, ?, ?)
       ON CONFLICT(assessment_id, question_id)
       DO UPDATE SET answer_value = excluded.answer_value;
       ```
     - Triggers `export_userdata_to_csv()` to reflect active draft status in `userdata.csv`.

---

### 3. Assessment Submission
When question 70 is completed, the candidate clicks **"SUBMIT ASSESSMENT 🚀"**:
1. Frontend verifies that all questions are answered.
2. Displays an animated processing modal with progress steps ("Fuzzifying 20 Traits...", "Evaluating 420 Mamdani Rules...", "Ranking 105 Careers...").
3. Dispatches payload:
   ```javascript
   const response = await fetch("/api/submit", {
     method: "POST",
     headers: { "Content-Type": "application/json" },
     body: JSON.stringify({
       user_id: 37,
       answers: { "Q1": 5, "Q2": 4, "Q3": 5, ..., "Q70": 4 }
     })
   });
   ```

---

## 🧮 PHASE 4: Core Analytical Backend Pipeline (`/api/submit`)

Upon receiving `POST /api/submit`, the backend executes the end-to-end mathematical pipeline in under **5 milliseconds**:

```
[ POST /api/submit ]
        │
        ├── 1. db.complete_assessment() ──> UPDATE assessments SET status='completed'
        │
        ├── 2. feature_extraction.py ──> Likert [1-5] to [0.0-10.0] Feature Normalization
        │
        ├── 3. fuzzy_engine.py ──> 420 Mamdani Rules & Centroid Defuzzification (0-100%)
        │
        ├── 4. recommendation_engine.py ──> Pearson Shape Fit + Weighted Deficit Matrix Math
        │
        ├── 5. Score Blending & Fit-Preserving Exponential Scaling (12% to 96%)
        │
        ├── 6. skill_gap_analysis.py ──> Δ = Required - User Score (Deficit Categorization)
        │
        ├── 7. roadmap_builder.py ──> 6-Step Curriculum Assembly & [PRIORITY] Tagging
        │
        ├── 8. db.save_results() ──> Persists JSON artifacts in SQLite results table
        │
        └── 9. userdata_exporter.py ──> Real-time sync of userdata.csv & user_attempts.csv
```

---

### Step 4.1: Feature Extraction & Likert Normalization (`feature_extraction.py`)
1. Maps the 70 responses to their respective skills ($Q_s$).
2. Calculates the mean rating $\bar{x}_s \in [1.0, 5.0]$.
3. Linearly normalizes to a continuous $[0.0, 10.0]$ scale:
   $$S_s = \frac{\bar{x}_s - 1.0}{4.0} \times 10.0$$
4. Computes confidence factor based on question density:
   $$\text{conf}_s = |Q_s|$$
5. Yields candidate skill vector $\mathbf{U} = [u_1, u_2, \dots, u_{20}]$ (e.g. `Programming: 9.5`, `Math: 9.0`, `Creativity: 4.2`...).

---

### Step 4.2: Mamdani Fuzzy Inference Engine (`fuzzy_engine.py`)
1. **Fuzzification**: Evaluates each skill score $u_s$ across 5 Triangular Membership Functions ($\mu_{\text{VL}}, \mu_{\text{L}}, \mu_{\text{M}}, \mu_{\text{H}}, \mu_{\text{VH}}$):
   $$\mu(x; a, b, c) = \max\left(0, \min\left(\frac{x - a}{b - a}, \frac{c - x}{c - b}\right)\right)$$
2. **Rule Base Evaluation (420 Rules)**: For each career, evaluates its 4 domain rules from `rules.csv`.
   - Computes antecedent conjunction using fuzzy Min T-norm:
     $$\alpha_k = \min\left( \mu_{A_{1k}}(u_1), \mu_{A_{2k}}(u_2), \mu_{A_{3k}}(u_3), \mu_{A_{4k}}(u_4) \right)$$
3. **Fuzzy Output Aggregation**: Computes the aggregated envelope using fuzzy Max S-norm:
   $$\mu_{\text{agg}}(y) = \max_k \left( \min(\alpha_k, \mu_{C_k}(y)) \right)$$
4. **Centroid Defuzzification**: Integrates over the continuous output universe ($0\text{--}100\%$):
   $$y^* = \frac{\int_{0}^{100} y \cdot \mu_{\text{agg}}(y) \, dy}{\int_{0}^{100} \mu_{\text{agg}}(y) \, dy}$$
   Yields the crisp rule-based compatibility score: $\text{FuzzyScore}_c \in [0.0, 100.0]$.

---

### Step 4.3: Pearson Shape Correlation & Deficit Matrix Scoring (`recommendation_engine.py`)
To evaluate full 20-dimensional aptitude without arithmetic masking:

1. **Pearson Profile Shape Correlation**: Measures geometric alignment between candidate vector $\mathbf{U}$ and career requirement vector $\mathbf{R}_c$:
   $$r = \frac{\sum_{s=1}^{20} (u_s - \bar{u})(r_{cs} - \bar{r}_c)}{\sigma_u \cdot \sigma_{rc}}$$
   $$\text{ShapeScore}_c = 50.0 + (r \times 50.0)$$

2. **Confidence-Weighted Deficit Penalty**:
   Applies a non-linear power curve $(r / 10.0)^{2.5}$ to heavily penalize missing core prerequisites:
   $$\text{conf\_factor}_s = \max\left(0.4, \min\left(1.0, \frac{\text{conf}_s}{3.0}\right)\right)$$
   $$w_s = \left(\frac{r_{cs}}{10.0}\right)^{2.5} \times \text{conf\_factor}_s$$
   $$\text{fit}_s = \begin{cases} 100.0 - (u_s - r_{cs}) \times 2.0 & \text{if } u_s \ge r_{cs} \\ \max\left(0.0, 100.0 - \frac{r_{cs} - u_s}{10.0} \times 160.0\right) & \text{if } u_s < r_{cs} \end{cases}$$
   $$\text{MatrixScore}_c = 0.50 \times \text{ShapeScore}_c + 0.50 \times \frac{\sum_{s=1}^{20} \text{fit}_s \cdot w_s}{\sum_{s=1}^{20} w_s}$$

---

### Step 4.4: Score Blending & Fit-Preserving Exponential Scaling
1. **Composite Score Blend**:
   $$\text{RawScore}_c = 0.45 \times \text{FuzzyScore}_c + 0.55 \times \text{MatrixScore}_c$$
2. **Fit-Preserving Exponential Scaling**:
   Normalizes the raw range and stretches it across $12.0\%\text{--}96.0\%$ using a $1.5$ exponent:
   $$\text{norm\_s} = \frac{\text{RawScore}_c - \min(\mathbf{Raw})}{\max(\mathbf{Raw}) - \min(\mathbf{Raw})}$$
   $$\text{Compatibility \%}_c = 12.0 + (\text{norm\_s}^{1.5}) \times (96.0 - 12.0)$$
3. Sorts all 105 careers descending to produce the complete ranking.

---

### Step 4.5: Skill Gap Analysis (`skill_gap_analysis.py`)
For each top recommendation:
1. Calculates skill deficit: $\Delta_s = \max(0.0, r_{cs} - u_s)$.
2. Classifies gaps:
   - $\Delta_s \ge 3.0 \to \textbf{Critical Deficit}$
   - $1.5 \le \Delta_s < 3.0 \to \textbf{Moderate Gap}$
   - $\Delta_s < 1.5 \to \textbf{Minor Refinement / Aligned}$

---

### Step 4.6: Dynamic Milestone Curriculum Assembly (`roadmap_builder.py`)
1. Pulls the 6 predefined milestone steps from `roadmaps.csv` for each top career.
2. Cross-references the step's `Skill Targeted` against the candidate's active skill deficits.
3. Automatically marks steps that address active deficits with `is_priority = True` (`[PRIORITY]`).

---

### Step 4.7: Database Commit & Real-Time CSV Synchronization
1. **SQLite Storage**:
   Executes `db.save_results(...)` saving serialized JSON strings to the `results` table.
2. **Real-Time CSV Export**:
   Invokes `export_userdata_to_csv()`:
   - Updates `data/userdata/userdata.csv` with total completed attempts, last attempt timestamp, and latest top 5 recommendations.
   - Appends new row to `data/userdata/user_attempts.csv` containing granular response count, timestamps, and compatibility percentages.
3. **HTTP Response**:
   Returns the full analytical JSON payload to `assessment.html`, which redirects to `results.html`.

---

## 📊 PHASE 5: Interactive Results Hub (`results.html`)

The candidate lands on the rich results dashboard.

```
┌────────────────────────────────────────────────────────────────────────┐
│                     CAREERLENS RESULTS DASHBOARD                       │
├────────────────────────────────────────────────────────────────────────┤
│  🏆 TOP 5 CAREER MATCHES (Cards with Match %, Salary, Rationale)       │
│  📋 6-STEP PERSONALISED ROADMAPS (Interactive Milestone Checkboxes)    │
│  🧪 "WHAT-IF?" SKILL SIMULATION LAB (Real-Time 60fps Dynamic Sliders)  │
│  ⚖️ SIDE-BY-SIDE CAREER COMPARATOR (Multi-Attribute Dock)              │
│  📄 PUBLICATION PDF REPORT EXPORT (ReportLab Multi-Page Vector PDF)    │
└────────────────────────────────────────────────────────────────────────┘
```

### 1. Top 5 Career Cards & Plain-Language Rationales
- Renders 5 interactive cards showing:
  - Career title & industry category badge.
  - Scaled compatibility percentage (e.g. `96.0%`).
  - Average Indian compensation (`12 LPA`), market demand (`Very High`), difficulty rating.
  - **Natural-Language Rationale**: "Recommended because: Programming, Math, and Logical Thinking."
  - 20-skill proficiency chips comparing candidate score vs benchmark requirement.

### 2. Interactive Roadmap & Live Progress Checkboxes
- Displays the 6-stage chronological learning pathway.
- Priority steps addressing verified skill gaps are highlighted with glowing badges.
- **Candidate clicks a checkbox** (e.g. Step 1: "Master Linear Algebra & NumPy"):
  - JavaScript captures the toggle, calculates completed ratio ($1/6 \to 16.7\%$), and animates the progress bar.
- **Click "Export to Notion / Markdown" Button**:
  - Compiles the complete curriculum into a formatted Markdown checklist and copies it to clipboard with a toast notification.

### 3. "What-If?" Skill Simulation Lab
- Features 20 interactive sliders representing each competency.
- **Candidate drags a slider** (e.g. boosting *Programming* from 5.0 to 9.5):
  1. Frontend client-side matrix engine recalculates compatibility scores for all 105 careers at 60fps without network latency.
  2. Updates career ranking in real-time.
  3. Displays live surge badges (e.g. `"+35% Match Surge for AI/ML Engineer"`).

### 4. Side-by-Side Career Comparator
- Allows candidate to pick 2 or 3 careers from the catalog dropdown.
- Renders comparison matrix contrasting required skills, compensation tiers, remote feasibility, and roadmap timelines.

### 5. ReportLab PDF Generation Button
- Candidate clicks **"DOWNLOAD PDF REPORT 📄"**:
  1. Frontend calls `GET /api/pdf/<user_id>` (or `GET /api/pdf/assessment/<assessment_id>`).
  2. Backend `app.py` triggers ReportLab compiler:
     - Assembles vector layout with candidate metadata, score distribution table, skill gap matrix, and 6-stage roadmap.
  3. Streams binary `application/pdf` attachment to the browser, prompting automatic file download.

---

## 📈 PHASE 6: Longitudinal Dashboard & Evolution Tracker (`dashboard.html`)

Candidate navigates to `dashboard.html` to review their long-term profile:

### 1. 20-Skill Chart.js Radar Chart
- Fetches latest assessment results via `GET /api/results/<user_id>`.
- Renders an interactive 20-axis Chart.js Radar polygon illustrating candidate strengths vs market averages.

### 2. Top 5 Compatibility Bar Chart
- Renders horizontal bar chart visualizing relative match strength across top vocational tracks.

### 3. Longitudinal Attempt Timeline & Evolution Badges
- Fetches all historical sessions via `GET /api/user/<user_id>/history`.
- Displays chronologically ordered attempt cards.
- Computes skill delta badges comparing Attempt #1 vs Attempt #2 (e.g. `"+1.5 gain in Logical Thinking"`).
- Candidate can click **"View Historical Result"** on any card to load that exact past report.

---

## 🔬 PHASE 7: Model Accuracy & Evaluation Framework (`evaluation.html`)

Accessible via the navbar ("System Score ↗") or at `http://localhost:5000/evaluation`:

### 1. Accuracy Metric Cards
Frontend calls `GET /api/evaluation/results` and renders live Information Retrieval metrics:
- **Top-1 Exact Match**: `65.71%` (69 / 105 careers).
- **Top-5 Hit Rate**: `92.38%` (97 / 105 careers placed in Top 5).
- **Top-5 Flexible Match**: `96.19%` (101 / 105 in candidate choice set).
- **Domain Category Alignment**: `84.76%` (Top-1) / `99.05%` (Top-5).
- **Mean Reciprocal Rank (MRR)**: `0.7788`.
- **Average Target Career Rank**: `#1.89` in 105 professions.

### 2. Interactive Buttons on Evaluation Dashboard
- **Click "Run Full Benchmark" Button**:
  - Sends `POST /api/evaluation/run`.
  - Backend executes `evaluation/evaluate_recommendations.py` across all 105 careers, recalculating metrics and regenerating `evaluation/results.csv`.
- **Click "Download Ground Truth Dataset CSV"**:
  - Streams `data/evaluation/ground_truth_demo.csv` via `GET /api/evaluation/download`.
- **Click "Download User Data CSV" / "Download Attempts CSV"**:
  - Streams `data/userdata/userdata.csv` via `GET /api/userdata/csv`.
  - Streams `data/userdata/user_attempts.csv` via `GET /api/userdata/attempts/csv`.

---

## 📑 Complete Master API Endpoint Reference

| Method | Endpoint | Trigger Source | Backend Handler | Database / System Action |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/register` | Click "Create Account" on `login.html` | `app.py -> register()` | Generates unique code (`SHASH-6722`), inserts into `users` table, syncs `userdata.csv`. |
| `POST` | `/api/login` | Click "Sign In" on `login.html` | `app.py -> login()` | Queries user by unique code, fetches historical attempts with top careers. |
| `POST` | `/api/assessment/draft` | Answering questions on `assessment.html` | `app.py -> save_draft()` | Upserts responses to `responses` table, marks assessment `in_progress`, syncs CSV. |
| `GET` | `/api/assessment/draft/<id>` | Loading `assessment.html` | `app.py -> get_draft()` | Fetches active draft responses to resume incomplete sessions. |
| `POST` | `/api/submit` | Click "Submit Assessment" on `assessment.html` | `app.py -> submit()` | Runs full fuzzy & matrix pipeline, marks completed, commits results JSON, syncs CSV. |
| `GET` | `/api/results/<id>` | Loading `results.html` / `dashboard.html` | `app.py -> get_results()` | Fetches latest assessment results, skill profile, top 5, gaps, and roadmaps. |
| `GET` | `/api/assessment/<id>/results`| Clicking past attempt card | `app.py -> get_assessment_results()` | Fetches results for a specific historical assessment session. |
| `GET` | `/api/user/<id>/history` | Loading timeline on `dashboard.html` | `app.py -> get_history()` | Returns chronological attempt list with top career badges. |
| `GET` | `/api/careers` | Comparator dropdowns on `results.html` | `app.py -> get_careers()` | Returns full 105-career catalog with salaries, demand, and education. |
| `GET` | `/api/pdf/<id>` | Click "Download PDF" on `results.html` | `app.py -> download_pdf()` | Compiles and streams ReportLab publication-grade multi-page PDF. |
| `GET` | `/api/userdata/csv` | Download button on evaluation / admin | `app.py -> download_userdata_csv()`| Regenerates and streams `data/userdata/userdata.csv`. |
| `GET` | `/api/userdata/attempts/csv` | Download button on evaluation / admin | `app.py -> download_user_attempts_csv()`| Regenerates and streams `data/userdata/user_attempts.csv`. |
| `GET` | `/api/userdata/export` | On-demand maintenance call | `app.py -> export_userdata_route()`| Runs `userdata_exporter.py` and returns JSON summary stats. |
| `GET` | `/api/evaluation/results` | Loading `evaluation.html` | `app.py -> get_evaluation_results()`| Returns IR benchmark metrics (Top-1, Top-5, MRR, NDCG). |
| `POST` | `/api/evaluation/run` | Click "Run Evaluation" on `evaluation.html`| `app.py -> run_evaluation()` | Executes benchmark script and refreshes evaluation results. |
| `GET` | `/api/health` | Automated monitoring probe | `app.py -> health()` | Returns `{ "status": "ok", "db": "path" }`. |

---

*CareerLens — Complete System & Operational Architecture Documentation.*
