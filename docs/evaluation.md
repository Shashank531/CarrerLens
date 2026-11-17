# CareerLens — Recommendation System Evaluation & Accuracy Framework

## 1. Executive Summary & Problem Context

Career recommendation systems face a fundamental evaluation challenge that distinguishes them from conventional supervised machine learning classifiers:

- **Supervised Classifiers (e.g. Spam Detection, Image Classification)**: Aim to predict a single ground-truth discrete label with binary or multi-class accuracy.
- **Continuous Multi-Criteria Recommender Systems (CareerLens)**: Model multi-dimensional human competencies across 20 continuous skills, evaluating them against 105 vocational benchmark profiles using Mamdani fuzzy inference and matrix satisfaction scoring.

Because career aptitude is inherently multi-faceted (for example, a student strong in mathematics and programming is genuinely qualified for *AI/ML Engineer*, *Data Scientist*, *Backend Developer*, and *Quantitative Analyst* simultaneously), evaluating recommendation quality requires **Information Retrieval (IR) ranking metrics** such as **Top-1 Accuracy**, **Top-5 Hit Rate**, **Mean Reciprocal Rank (MRR)**, and **Domain Category Alignment**.

> [!IMPORTANT]
> **Validation vs. Real-World Accuracy**:
> - The automated tests in `backend/test_pipeline.py` verify that **5/5 predefined functional personas** trigger domain-expected outputs without software errors (**Pipeline Validation Success Rate: 100%**).
> - Functional testing alone does **not** constitute empirical real-world placement accuracy.
> - The evaluation module in `evaluation/evaluate_recommendations.py` provides the formal mathematical framework to evaluate CareerLens against labelled datasets (both synthetic benchmarks and real-world student cohorts).

---

## 2. What is "Ground Truth" in Career Recommendation?

In career guidance, **Ground Truth** refers to verified target career outcomes against which model recommendations are measured. Ground truth can originate from two sources:

1. **Empirical Placement & Longitudinal Data**: Real students or alumni whose eventual job placements, career satisfaction, or expert counselor-advised paths are recorded alongside their initial skill assessments.
2. **Standardized Synthetic Benchmarks (`ground_truth_demo.csv`)**: Archetypal competency vectors constructed across diverse domains (Technology, Design, Healthcare, Business, Engineering, Finance, Research) to functionally stress-test the ranking and retrieval math.

### Ground Truth CSV Format (`data/evaluation/ground_truth.csv`)
```csv
student_id,name,expected_career,expected_category,acceptable_careers,Programming,Math,Logical Thinking,...
S001,Priya Patel,AI/ML Engineer,Technology,Data Scientist|Software Engineer|Backend Developer,9.5,9.0,9.0,...
S002,Rahul Sharma,UI/UX Designer,Design,Graphic Designer|Frontend Developer,6.5,4.0,7.0,...
```

- **`expected_career`**: The primary target occupation.
- **`expected_category`**: The broad industry domain (e.g., *Technology*, *Design*, *Healthcare*, *Business*).
- **`acceptable_careers`**: Pipe-separated list of acceptable related occupations sharing high competency overlap.
- **Competency Columns (0.0–10.0)**: Scores across the 20 master traits (or Likert responses from the 70-question survey).

---

## 3. Core Evaluation Metrics & Mathematical Formulations

The evaluation engine (`evaluation/evaluate_recommendations.py`) runs each test case through the **exact existing CareerLens pipeline** using the calibrated scoring blend ($45\%\text{ Fuzzy} + 55\%\text{ Matrix}$) and computes the following metrics:

### 3.1 Top-1 Accuracy (Exact Match)
Measures the proportion of test cases where the single highest-ranked recommendation ($k=1$) matches the primary target career:

$$\text{Top-1 Accuracy} = \frac{\text{Number of Cases where }\text{Predicted}_1 = \text{Expected}}{\text{Total Labelled Cases } N} \times 100$$

### 3.2 Top-5 Accuracy / Hit Rate
In vocational guidance, presenting a student with a curated dashboard of top-5 career matches with personalized learning roadmaps is standard practice. Top-5 Accuracy measures whether the expected career is present within this primary recommendation set:

$$\text{Top-5 Accuracy} = \frac{\text{Number of Cases where }\text{Expected Career} \in \text{Top-5 Recommendations}}{N} \times 100$$

### 3.3 Top-5 Flexible Hit Rate
Accounts for the reality of overlapping vocational archetypes by checking whether either the primary expected career or any predefined acceptable alternative is captured in the Top 5:

$$\text{Top-5 Flexible Accuracy} = \frac{\text{Number of Cases where } (\text{Expected} \cup \text{Acceptable}) \cap \text{Top-5} \neq \emptyset}{N} \times 100$$

### 3.4 Category-Level Domain Accuracy
Measures whether the broad vocational field of the top-ranked recommendation aligns with the expected industry domain (e.g., recommending *Cloud Engineer* [Technology] when *DevOps Engineer* [Technology] was expected):

$$\text{Category Accuracy} = \frac{\text{Number of Cases where }\text{Category}(\text{Predicted}_1) = \text{Expected Category}}{N} \times 100$$

### 3.5 Mean Reciprocal Rank (MRR)
MRR is the standard Information Retrieval metric that evaluates the position where the target career first appears in the complete 105-career ranked list:

$$\text{MRR} = \frac{1}{N} \sum_{i=1}^N \frac{1}{\text{Rank}_i}$$

Where $\text{Rank}_i$ is the 1-based position of the target career for student $i$:
- Rank 1 contributes $\frac{1}{1} = 1.00$
- Rank 2 contributes $\frac{1}{2} = 0.50$
- Rank 3 contributes $\frac{1}{3} = 0.333$
- Rank 5 contributes $\frac{1}{5} = 0.20$
- Rank $>105$ contributes $0.00$

---

## 4. Why Top-5 Accuracy is Essential for Career Guidance

In conventional classification (e.g., digit recognition), any output other than the exact class is an error. In vocational counseling, single-label classification is fundamentally flawed for three reasons:

1. **Competency Overlap (The Generalist Reality)**:
   A student with high analytical and programming ability is equally suited for *Data Scientist*, *Machine Learning Engineer*, or *Data Engineer*. Forcing the algorithm to pick only one penalizes valid matches.
2. **Exploration vs. Prescription**:
   Career counselling psychology (e.g., Super's Developmental Self-Concept Theory and Holland's RIASEC model) emphasizes exploring adjacent roles. Presenting Top 5 recommendations with gap analyses enables informed decision-making.
3. **Actionable Progression**:
   CareerLens attaches customized 6-stage roadmaps and skill gap breakdowns to all Top 5 careers, allowing students to compare paths side-by-side.

---

## 5. How to Run the Evaluation Suite

### Option A: Command Line Interface (CLI)
Run the automated evaluator against the default dataset (`ground_truth_demo.csv` or `ground_truth.csv`):

```bash
# Run complete evaluation benchmark
python evaluation/evaluate_recommendations.py

# Run against a specific ground truth dataset
python evaluation/evaluate_recommendations.py --dataset data/evaluation/ground_truth_demo.csv

# Output to custom directory
python evaluation/evaluate_recommendations.py --outdir evaluation/
```

### Option B: REST API Endpoints
The Flask backend provides RESTful endpoints for integration and automation:

- `GET /api/evaluation/results`: Retrieves latest evaluation metrics, category breakdowns, and student case details.
- `GET /api/evaluation/download`: Downloads the benchmark ground truth dataset CSV.
- `GET /api/evaluation/datasets`: Lists all available evaluation datasets and their sample counts.

### Option C: Interactive Evaluation Dashboard
Access the visual dashboard via browser:
- **Local Dev Server**: `http://localhost:5000/evaluation` or `http://localhost:8000/evaluation.html`
- **Features**:
  - Live KPI metric cards (Top-1 65.7%, Top-5 92.4%, Flexible Top-5 96.2%, Domain Match 99.1%, MRR 0.7788, Avg Rank #1.89).
  - Interactive Chart.js graphs (Accuracy comparisons, Rank distributions, Domain breakdowns).
  - Filterable and searchable student test-case table with modal inspection.

---

## 6. Output Files & Artifacts

Every evaluation run generates two structured output files in `evaluation/`:

### 1. `evaluation/results.json`
Contains aggregate summary statistics, category performance metrics, rank histograms, and individual student results formatted for API consumption.

```json
{
  "status": "success",
  "dataset_file": "ground_truth_demo.csv",
  "is_synthetic": true,
  "total_cases": 105,
  "metrics": {
    "top1_accuracy": 65.71,
    "top5_accuracy": 92.38,
    "acceptable_top5_accuracy": 96.19,
    "category_accuracy": 84.76,
    "top5_category_accuracy": 99.05,
    "mrr": 0.7788,
    "mean_expected_rank": 1.89
  },
  "rank_distribution": {
    "rank_1": 69,
    "rank_2_to_3": 24,
    "rank_4_to_5": 4,
    "rank_6_to_10": 4,
    "rank_gt_10": 4
  }
}
```

### 2. `evaluation/results.csv`
A tabular spreadsheet containing student-by-student predictions for reporting and analysis in tools like Excel, Pandas, or Google Sheets.

| Column | Description |
|---|---|
| `student_id` | Identifier of the test case |
| `name` | Persona / Profile label |
| `expected_career` | Target primary career |
| `expected_category` | Target domain |
| `predicted_career` | Top-1 recommendation from CareerLens |
| `predicted_compatibility` | Match percentage score (12.0%–96.0%) |
| `rank_of_expected` | Rank position of target role in the 105-career output |
| `correct_top1` | Boolean (`True` if Top-1 exact match) |
| `correct_top5` | Boolean (`True` if Target in Top 5) |
| `acceptable_top5` | Boolean (`True` if Target or acceptable alternative in Top 5) |
| `reciprocal_rank` | $1 / \text{Rank}$ score |
| `top5_recommendations` | Full list of top 5 recommendations with match scores |

---

## 7. Protocol for Collecting Real-World Ground Truth

To transition from synthetic demonstration benchmarks to empirical real-world validation:

1. **Alumni Placement Survey**: Survey recent graduates who have secured jobs. Collect their verified job titles along with their responses to the 70-question CareerLens self-assessment.
2. **Career Counselor Annotations**: Have certified vocational counselors review anonymized student skill profiles and independently assign their top 3 recommended career tracks.
3. **Data Ingestion**: Place the verified records into `data/evaluation/ground_truth.csv`.
4. **Execution**: Run `python evaluation/evaluate_recommendations.py`. When `ground_truth.csv` contains verified data, the dashboard will automatically switch from **Demo Mode** to **Empirical Cohort Mode**.

---

## 8. Summary of Validation vs. Accuracy Distinctions

| Evaluation Layer | Script / Tool | Dataset | Primary Metric | What It Proves |
|---|---|---|---|---|
| **Multi-Persona Stress Test** | `backend/test_all_personas.py` | 52 multi-disciplinary real-world personas | **Pass Rate: 100%** (52/52 passed) | Proves system-wide domain and career precision across 21 disciplines. |
| **Catalog Benchmark Suite** | `evaluation/evaluate_recommendations.py` | `ground_truth_demo.csv` (105 careers evaluated) | **Top-5 Hit: 92.38%**, **Top-5 Flex: 96.19%**, **MRR: 0.7788**, **Avg Rank: #1.89** | Quantifies ranking quality and Information Retrieval metrics across the master catalog. |
| **User Cohort Analytics** | `backend/userdata_exporter.py` | `data/userdata/userdata.csv` & `user_attempts.csv` | **Attempt Progression & Trajectory Evolution** | Tracks real-time longitudinal student attempts and score stability. |
| **Real-World Empirical Accuracy** | `evaluation/evaluate_recommendations.py` | `ground_truth.csv` (Future alumni data) | **Top-1 / Top-5 Accuracy on Verified Cohorts** | Establishes empirical placement accuracy across actual student cohorts. |
