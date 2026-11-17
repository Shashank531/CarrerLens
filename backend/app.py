"""
CareerLens — app.py
====================
Flask backend that wires together all phases (1–9) and exposes
the API routes the frontend calls via fetch().

Routes:
    POST /api/register          — create user, get back user_id + unique_code
    POST /api/login             — login by unique_code, get back user info + history
    POST /api/submit            — save answers, run full pipeline, return results
    GET  /api/results/<user_id> — fetch latest saved results for a user

Run:cd backend
python app.py
    pip install flask flask-cors
    python app.py
"""

import sys
import json
import random
import string
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS

# ── path setup so backend imports work when app.py is in backend/ ──
BASE   = Path(__file__).parent
DATA   = BASE.parent / "data" / "csv"

sys.path.insert(0, str(BASE))
from database            import Database
from feature_extraction  import load_questions, extract_features, skill_confidence
from fuzzy_engine        import FuzzyEngine
from recommendation_engine import RecommendationEngine
from skill_gap_analysis  import SkillGapAnalyzer
from roadmap_builder     import RoadmapBuilder
from userdata_exporter   import export_userdata_to_csv

# ── init ──────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)   # allow the HTML frontend to call us from file:// or localhost

DB_PATH   = BASE / "careerlens.db"
db        = Database(str(DB_PATH))
db.init_schema()

# Export initial userdata CSV on startup
try:
    export_userdata_to_csv(str(DB_PATH))
except Exception as e:
    print(f"[Warning] Failed initial userdata CSV export: {e}")

QUESTIONS        = load_questions(str(DATA / "questions.csv"))
SKILL_CONFIDENCE = skill_confidence(QUESTIONS)
fuzzy            = FuzzyEngine(data_dir=str(DATA))
rec_engine       = RecommendationEngine(data_dir=str(DATA))
gap_analyzer     = SkillGapAnalyzer(data_dir=str(DATA))
roadmap_builder  = RoadmapBuilder(data_dir=str(DATA))


# ── helpers ───────────────────────────────────────────────────────
def _generate_code(name: str) -> str:
    """
    Returns a unique login code like  ARJUN-4827
    (first 5 chars of name, uppercased, + hyphen + 4 random digits).
    """
    prefix = "".join(c for c in name.upper() if c.isalpha())[:5]
    digits = "".join(random.choices(string.digits, k=4))
    return f"{prefix}-{digits}"


def _err(msg: str, code: int = 400):
    return jsonify({"error": msg}), code


# ── routes ────────────────────────────────────────────────────────

@app.route("/api/register", methods=["POST"])
def register():
    """
    Body: { "name": "Arjun", "education": "B.Tech" }   (education optional)
    Returns: { "user_id": 3, "unique_code": "ARJUN-4827", "name": "Arjun" }
    """
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return _err("name is required")

    education = (data.get("education") or "").strip() or None

    # generate a unique code; retry on collision (extremely rare)
    for _ in range(10):
        code = _generate_code(name)
        if not db.get_user_by_code(code):
            break

    user_id = db.create_user(name=name, education=education, unique_code=code)
    try:
        export_userdata_to_csv(str(DB_PATH))
    except Exception as e:
        print(f"[Warning] Failed to export userdata CSV: {e}")
    return jsonify({"user_id": user_id, "unique_code": code, "name": name}), 201


@app.route("/api/login", methods=["POST"])
def login():
    """
    Body: { "unique_code": "ARJUN-4827" }
    Returns: { "user_id": 3, "name": "Arjun", "history": [...] }
    """
    data = request.get_json(silent=True) or {}
    code = (data.get("unique_code") or "").strip().upper()
    if not code:
        return _err("unique_code is required")

    user = db.get_user_by_code(code)
    if not user:
        return _err("No account found with that code. Check the code and try again.", 404)

    history = db.get_user_history(user["id"])
    return jsonify({
        "user_id":     user["id"],
        "name":        user["name"],
        "education":   user["education"],
        "unique_code": user["unique_code"],
        "history":     history,
    })


@app.route("/api/assessment/draft", methods=["POST"])
def save_draft():
    """
    Body: {
        "user_id": 3,
        "answers": { "Q1": 4, "Q2": 5, ... }
    }
    Saves in-progress draft responses for an uncompleted assessment.
    """
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    answers = data.get("answers", {})

    if not user_id:
        return _err("user_id is required")

    answers = {str(k): int(v) for k, v in answers.items()}
    assessment_id = db.save_draft(int(user_id), answers)
    try:
        export_userdata_to_csv(str(DB_PATH))
    except Exception as e:
        print(f"[Warning] Failed to export userdata CSV: {e}")
    return jsonify({
        "status": "saved",
        "assessment_id": assessment_id,
        "count": len(answers)
    })


@app.route("/api/assessment/draft/<int:user_id>", methods=["GET"])
def get_draft(user_id: int):
    """
    Retrieves in-progress assessment draft responses for a user if present.
    """
    draft = db.get_draft(user_id)
    if not draft:
        return jsonify({"draft": None, "has_draft": False})
    return jsonify({"draft": draft, "has_draft": True})


@app.route("/api/submit", methods=["POST"])
def submit():
    """
    Body: {
        "user_id": 3,
        "answers": { "Q1": 4, "Q2": 5, ... }
    }
    Runs the full pipeline and returns results + saves to DB.
    Returns: { "skill_profile": {...}, "top5": [...], "skill_gaps": {...}, "roadmaps": {...} }
    """
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    answers  = data.get("answers", {})

    if not user_id:
        return _err("user_id is required")
    if len(answers) < 10:
        return _err("Too few answers submitted")

    # convert string keys to expected format
    answers = {str(k): int(v) for k, v in answers.items()}

    # ── pipeline ──
    assessment_id = db.start_assessment(user_id)
    db.save_responses(assessment_id, answers)
    db.complete_assessment(assessment_id)

    skill_profile = extract_features(answers, QUESTIONS)
    ranked        = fuzzy.score_all(skill_profile, confidence=SKILL_CONFIDENCE)
    top5          = rec_engine.recommend(skill_profile, ranked, top_n=5)

    # Compute full score ranking for all 105 careers
    all_scores = {r["career"]: r["compatibility"] for r in ranked}

    # top 30 — lightweight list (no explanation/roadmap, just name + score)
    top30 = [
        {"career": r["career"], "compatibility": r["compatibility"]}
        for r in ranked[:30]
    ]

    # skill gaps + roadmaps for each top career
    skill_gaps = {}
    roadmaps   = {}
    for career in top5:
        name = career["career"]
        gaps = gap_analyzer.analyze(name, skill_profile)
        skill_gaps[name] = gaps
        roadmaps[name]   = roadmap_builder.build(name, gaps)

    db.save_results(assessment_id, skill_profile, top5, top30, skill_gaps, roadmaps)

    try:
        export_userdata_to_csv(str(DB_PATH))
    except Exception as e:
        print(f"[Warning] Failed to export userdata CSV: {e}")

    return jsonify({
        "assessment_id": assessment_id,
        "skill_profile": skill_profile,
        "top5":          top5,
        "top30":         top30,
        "all_scores":    all_scores,
        "skill_gaps":    skill_gaps,
        "roadmaps":      roadmaps,
    })



def _hydrate_result(result: dict) -> dict:
    """
    Ensures top30, all_scores, skill_gaps, and roadmaps are computed with the latest 
    personalized roadmap definitions from roadmaps.csv for all assessments.
    """
    if not result:
        return result
    skill_profile = result.get("skill_profile", {})
    
    # Calculate full 105-career score map
    ranked = fuzzy.score_all(skill_profile, confidence=SKILL_CONFIDENCE)
    result["all_scores"] = {r["career"]: r["compatibility"] for r in ranked}
    
    if not result.get("top30"):
        result["top30"] = [
            {"career": r["career"], "compatibility": r["compatibility"]}
            for r in ranked[:30]
        ]

    top5 = result.get("top5", [])
    computed_gaps = result.get("skill_gaps") or {}
    computed_roadmaps = {}

    for career in top5:
        name = career["career"]
        gaps = computed_gaps.get(name) or gap_analyzer.analyze(name, skill_profile)
        computed_gaps[name] = gaps
        # Build fresh, personalized roadmap for this career and user gaps
        roadmap = roadmap_builder.build(name, gaps)
        computed_roadmaps[name] = roadmap
        career["roadmap"] = roadmap
        career["skill_gaps"] = gaps

    result["skill_gaps"] = computed_gaps
    result["roadmaps"] = computed_roadmaps

    return result


@app.route("/api/results/<int:user_id>", methods=["GET"])
def get_results(user_id):
    """
    Returns the latest saved results for a user (for dashboard / history view).
    """
    result = db.get_latest_result(user_id)
    if not result:
        return _err("No results found for this user", 404)
    return jsonify(_hydrate_result(result))


@app.route("/api/user/<int:user_id>/history", methods=["GET"])
@app.route("/api/history/<int:user_id>", methods=["GET"])
def get_history(user_id):
    """
    Returns all assessments for a user with status, timestamps, and top careers.
    """
    history = db.get_user_history(user_id)
    return jsonify(history)


@app.route("/api/assessment/<int:assessment_id>/results", methods=["GET"])
@app.route("/api/results/assessment/<int:assessment_id>", methods=["GET"])
def get_assessment_results(assessment_id):
    """
    Returns the specific assessment results by assessment_id (for viewing old vs updated report).
    """
    result = db.get_results(assessment_id)
    if not result:
        return _err("No results found for this assessment", 404)
    return jsonify(_hydrate_result(result))


@app.route("/api/careers", methods=["GET"])
def get_careers():
    """
    Returns the full list of careers from careers.csv as a JSON array.
    Each element has keys: career_id, career, category, description,
    future_demand, avg_salary_lpa, difficulty, required_education,
    remote_work, growth_rate, industry.
    """
    import csv
    careers_path = DATA / "careers.csv"
    careers = []
    try:
        with open(careers_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                careers.append({
                    "career_id":         row.get("Career ID", ""),
                    "career":            row.get("Career Name", ""),
                    "category":          row.get("Category", ""),
                    "description":       row.get("Description", ""),
                    "future_demand":     row.get("Future Demand", ""),
                    "avg_salary_lpa":    row.get("Avg Salary (LPA)", ""),
                    "difficulty":        row.get("Difficulty", ""),
                    "required_education": row.get("Required Education", ""),
                    "remote_work":       row.get("Remote Work", ""),
                    "growth_rate":       row.get("Growth Rate", ""),
                    "industry":          row.get("Industry", ""),
                })
    except FileNotFoundError:
        return _err("careers.csv not found", 500)
    return jsonify(careers)


def generate_pdf_response(result, user, assessment_id):
    import io
    import math
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from datetime import datetime

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image, PageBreak, KeepTogether
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
    from flask import make_response

    result = _hydrate_result(result)

    skill_profile = result.get("skill_profile", {})
    top5 = result.get("top5", [])
    top30 = result.get("top30", [])
    skill_gaps = result.get("skill_gaps", {})
    roadmaps = result.get("roadmaps", {})
    user_id = user["id"] if user and "id" in user else result.get("user_id", "0")
    aid = assessment_id or result.get("assessment_id", "0")

    # Construct Top 10 with metadata
    top10 = []
    top_source = top30 if (top30 and len(top30) >= 10) else top5
    for item in top_source[:10]:
        c_name = item.get("career")
        meta = rec_engine.career_meta.get(c_name, {})
        top10.append({
            "career": c_name,
            "compatibility": float(item.get("compatibility") or item.get("score") or 75.0),
            "category": meta.get("category", "General"),
            "salary": str(meta.get("salary", "8")) + " LPA",
            "demand": meta.get("demand", "High"),
            "education": meta.get("education", "Bachelors")
        })

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.2*cm,
        leftMargin=1.2*cm,
        topMargin=1.2*cm,
        bottomMargin=1.2*cm
    )

    # Theme palette
    RUST = HexColor("#C45A32")
    INK = HexColor("#1C1A16")
    DUST = HexColor("#736B5E")
    LIGHT = HexColor("#F9F7F2")
    SAND = HexColor("#EBE5DA")
    WHITE = HexColor("#FFFFFF")
    GREEN = HexColor("#2D6A4F")
    ACCENT = HexColor("#8B381A")

    styles = getSampleStyleSheet()

    p_title = ParagraphStyle("DocTitle", fontName="Helvetica-Bold", fontSize=20, textColor=INK, leading=24, spaceAfter=2)
    p_sub = ParagraphStyle("DocSub", fontName="Helvetica", fontSize=8.5, textColor=DUST, leading=11, spaceAfter=6)
    p_sec = ParagraphStyle("SecHead", fontName="Helvetica-Bold", fontSize=12, textColor=RUST, leading=15, spaceBefore=8, spaceAfter=4)
    p_card_head = ParagraphStyle("CardHead", fontName="Helvetica-Bold", fontSize=10, textColor=INK, leading=13, spaceAfter=1)
    p_body = ParagraphStyle("BodyText", fontName="Helvetica", fontSize=8, textColor=INK, leading=11)
    p_small = ParagraphStyle("SmallText", fontName="Helvetica", fontSize=7, textColor=DUST, leading=9)
    p_badge = ParagraphStyle("BadgeText", fontName="Helvetica-Bold", fontSize=7.5, textColor=RUST, leading=9)
    p_step_title = ParagraphStyle("StepTitle", fontName="Helvetica-Bold", fontSize=8, textColor=INK, leading=10)
    p_step_desc = ParagraphStyle("StepDesc", fontName="Helvetica", fontSize=7.5, textColor=DUST, leading=10)

    story = []

    # ── Header ──
    date_str = datetime.now().strftime("%d %b %Y")
    u_code = user.get("unique_code", "CAREERLENS") if user else "CAREERLENS"
    u_name = user.get("name", "Candidate") if user else "Candidate"
    u_edu = user.get("education", "Not Specified") if user else "Not Specified"

    h_data = [
        [
            Paragraph('<b>CAREERLENS</b><br/><font size=7.5 color="#736B5E">Precision Cognitive AI Vocational Evaluation</font>', p_title),
            Paragraph(f'<b>Candidate Report</b><br/><font size=7.5 color="#736B5E">Code: <b>{u_code}</b><br/>Date: {date_str}</font>', ParagraphStyle('RightH', fontName='Helvetica', fontSize=8.5, textColor=INK, alignment=TA_RIGHT, leading=12))
        ]
    ]
    t_head = Table(h_data, colWidths=[11.5*cm, 7.1*cm])
    t_head.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('PADDING', (0,0), (-1,-1), 0)]))
    story.append(t_head)
    story.append(HRFlowable(width="100%", thickness=1.5, color=RUST, spaceBefore=6, spaceAfter=8))

    # ── User Info Box ──
    top_c_name = top5[0]["career"] if top5 else "Candidate Trajectory"
    top_c_fit = f"{top5[0]['compatibility']:.1f}%" if top5 else "96.0%"
    u_info = [
        [
            Paragraph(f'<b>Candidate:</b> {u_name}', p_body),
            Paragraph(f'<b>Education:</b> {u_edu}', p_body),
            Paragraph(f'<b>Assessment ID:</b> #{aid}', p_body),
            Paragraph(f'<b>Top Match:</b> <font color="#C45A32"><b>{top_c_name} ({top_c_fit})</b></font>', p_body)
        ]
    ]
    t_user = Table(u_info, colWidths=[5.0*cm, 5.0*cm, 3.8*cm, 4.8*cm])
    t_user.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), LIGHT),
        ('BOX', (0,0), (-1,-1), 0.5, SAND),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
    ]))
    story.append(t_user)
    story.append(Spacer(1, 0.3*cm))

    # ── Render Visual Charts ──
    # Radar Chart
    skills_sorted = sorted(skill_profile.keys()) if skill_profile else ["General"]
    scores_sorted = [float(skill_profile[s]) for s in skills_sorted] if skill_profile else [5.0]
    N = len(skills_sorted)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]
    scores_plot = scores_sorted + scores_sorted[:1]

    fig, ax = plt.subplots(figsize=(4.2, 4.2), subplot_kw=dict(polar=True), dpi=220)
    fig.patch.set_facecolor('#FDFBF7')
    ax.set_facecolor('#FDFBF7')
    ax.plot(angles, scores_plot, color='#C45A32', linewidth=1.6, linestyle='solid')
    ax.fill(angles, scores_plot, color='#C45A32', alpha=0.22)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels([s.replace(' ', '\n') for s in skills_sorted], size=5.5, color='#1C1A16', fontweight='bold')
    ax.set_ylim(0, 10)
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(['2', '4', '6', '8', '10'], size=5, color='#8C8577')
    ax.grid(color='#D8D0C5', linestyle='--', linewidth=0.5)
    ax.spines['polar'].set_color('#C45A32')
    radar_buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(radar_buf, format='png', bbox_inches='tight', facecolor=fig.get_facecolor(), dpi=220)
    plt.close(fig)
    radar_buf.seek(0)

    # Bar Chart
    fig2, ax2 = plt.subplots(figsize=(4.2, 2.3), dpi=220)
    fig2.patch.set_facecolor('#FDFBF7')
    ax2.set_facecolor('#FDFBF7')
    b_names = [c['career'] for c in top5] if top5 else ["Career 1"]
    b_scores = [float(c['compatibility']) for c in top5] if top5 else [80.0]
    y_pos = range(len(b_names))
    bars = ax2.barh(y_pos, b_scores, color='#C45A32', height=0.52, edgecolor='#8B381A', linewidth=0.7)
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(b_names, fontsize=7, fontweight='bold', color='#1C1A16')
    ax2.invert_yaxis()
    ax2.set_xlim(0, 108)
    ax2.set_xlabel('Fit Score (%)', fontsize=6.5, color='#8C8577', fontweight='bold')
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.spines['left'].set_color('#D8D0C5')
    ax2.spines['bottom'].set_color('#D8D0C5')
    ax2.tick_params(axis='x', colors='#8C8577', labelsize=6)
    ax2.grid(axis='x', color='#D8D0C5', linestyle='--', linewidth=0.5, alpha=0.6)
    for bar in bars:
        w = bar.get_width()
        ax2.text(w + 1.2, bar.get_y() + bar.get_height()/2, f'{w:.1f}%', va='center', ha='left', fontsize=6.5, fontweight='bold', color='#C45A32')
    bar_buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(bar_buf, format='png', bbox_inches='tight', facecolor=fig2.get_facecolor(), dpi=220)
    plt.close(fig2)
    bar_buf.seek(0)

    # Strengths & Weaknesses Table
    sorted_prof = sorted(skill_profile.items(), key=lambda x: -float(x[1])) if skill_profile else []
    top_str = sorted_prof[:5] if len(sorted_prof) >= 5 else sorted_prof
    bot_grw = sorted_prof[-5:] if len(sorted_prof) >= 5 else sorted_prof

    sw_rows = [
        [
            Paragraph('<b>Top Standout Strengths</b>', ParagraphStyle('ST', fontName='Helvetica-Bold', fontSize=8, textColor=GREEN)),
            Paragraph('<b>Key Growth Opportunities</b>', ParagraphStyle('GT', fontName='Helvetica-Bold', fontSize=8, textColor=RUST))
        ]
    ]
    for i in range(min(5, len(top_str))):
        s_name, s_val = top_str[i]
        g_name, g_val = bot_grw[i]
        sw_rows.append([
            Paragraph(f'• <b>{s_name}</b>: {float(s_val):.1f} / 10', p_body),
            Paragraph(f'• <b>{g_name}</b>: {float(g_val):.1f} / 10', p_body)
        ])
    t_sw = Table(sw_rows, colWidths=[4.5*cm, 4.5*cm])
    t_sw.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), LIGHT),
        ('PADDING', (0,0), (-1,-1), 3),
        ('GRID', (0,0), (-1,-1), 0.3, SAND)
    ]))

    # 2-column layout on Page 1
    col_left = Image(radar_buf, width=8.8*cm, height=8.8*cm)
    right_elements = [
        Image(bar_buf, width=8.8*cm, height=4.5*cm),
        Spacer(1, 0.2*cm),
        t_sw
    ]
    t_p1_grid = Table([[col_left, right_elements]], colWidths=[9.3*cm, 9.3*cm])
    t_p1_grid.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 0)
    ]))
    story.append(t_p1_grid)

    # ── Page 2: Top 10 Career Navigator & Top 3 Deep Dive ──
    story.append(PageBreak())
    story.append(Paragraph('Top 10 Career Trajectory Navigator', p_sec))
    story.append(Paragraph('Ranked using Mamdani Fuzzy Inference blended with Profile Shape Correlation across 105 industry profiles.', p_sub))

    t10_data = [
        ['#', 'Career Title', 'Industry Field', 'Avg Salary', 'Market Demand', 'Compatibility']
    ]
    for i, c in enumerate(top10, 1):
        c_score = float(c['compatibility'])
        t10_data.append([
            f'#{i}',
            c['career'],
            c['category'],
            c['salary'],
            c['demand'],
            f'{c_score:.1f}%'
        ])
    t_nav = Table(t10_data, colWidths=[1.0*cm, 5.5*cm, 3.6*cm, 2.5*cm, 3.0*cm, 3.0*cm])
    t_nav.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), RUST),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 7.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LIGHT]),
        ('GRID', (0,0), (-1,-1), 0.3, SAND),
        ('PADDING', (0,0), (-1,-1), 3.5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
    ]))
    story.append(t_nav)
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph('Primary Recommended Profiles & Skill Deficit Analysis', p_sec))
    for i, c in enumerate(top5[:3], 1):
        c_name = c['career']
        c_match = float(c['compatibility'])
        
        card_header = [
            [
                Paragraph(f'<b>#{i}. {c_name}</b> &nbsp;<font color="#C45A32"><b>{c_match:.1f}% Fit</b></font>', p_card_head),
                Paragraph(f'<font size=7 color="#736B5E">{c.get("category", "")} | {c.get("avg_salary_lpa", "")} LPA | Demand: {c.get("future_demand", "")}</font>', ParagraphStyle('CR', alignment=TA_RIGHT))
            ]
        ]
        t_ch = Table(card_header, colWidths=[11.0*cm, 7.6*cm])
        t_ch.setStyle(TableStyle([('PADDING', (0,0), (-1,-1), 0), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
        story.append(t_ch)
        story.append(Paragraph(f'<i>{c.get("explanation", "")}</i>', p_body))
        
        gaps = skill_gaps.get(c_name, [])
        if gaps:
            gap_rows = [['Skill', 'Yours', 'Req.', 'Deficit', 'Priority Level']]
            for g in gaps[:4]:
                sev = 'CRITICAL' if float(g['gap']) >= 2.5 else ('MODERATE' if float(g['gap']) >= 1.0 else 'MINOR')
                gap_rows.append([
                    g['skill'],
                    f"{float(g['user_score']):.1f}",
                    f"{float(g['required_score']):.1f}",
                    f"+{float(g['gap']):.1f}",
                    sev
                ])
            t_gap = Table(gap_rows, colWidths=[5.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 5.6*cm])
            t_gap.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), INK),
                ('TEXTCOLOR', (0,0), (-1,0), WHITE),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 7.5),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [LIGHT, WHITE]),
                ('GRID', (0,0), (-1,-1), 0.3, SAND),
                ('PADDING', (0,0), (-1,-1), 3),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
            ]))
            story.append(Spacer(1, 0.1*cm))
            story.append(t_gap)
        story.append(Spacer(1, 0.25*cm))

    # ── Page 3: Full 6-Stage Learning Roadmap ──
    story.append(PageBreak())
    top_pick_career = top5[0]['career'] if top5 else "Target Profession"
    story.append(Paragraph(f'Personalized Learning Roadmap: {top_pick_career}', p_sec))
    story.append(Paragraph(f'6-Stage prerequisite-aware developmental curriculum dynamically prioritized for {u_name}\'s profile deficits.', p_sub))

    curriculum = roadmaps.get(top_pick_career, [])
    for step in curriculum:
        s_order = step.get('step_order', 1)
        s_phase = step.get('phase', f'Stage {s_order}')
        s_text = step.get('step', '')
        s_dur = step.get('duration', '4-6 weeks')
        s_res = step.get('resource_type', 'Course')
        s_ms = step.get('milestone', False)
        s_prio = step.get('is_priority', False)
        
        badge_html = ''
        if s_prio:
            badge_html += ' <font color="#C45A32"><b>[PRIORITY SKILL GAP]</b></font>'
        if s_ms:
            badge_html += ' <font color="#2D6A4F"><b>[KEY MILESTONE]</b></font>'
            
        s_card = [
            [
                Paragraph(f'<b>STAGE {s_order}: {s_phase.upper()}</b> &nbsp; <font color="#736B5E">({s_dur} · {s_res})</font>{badge_html}', p_step_title)
            ],
            [
                Paragraph(s_text, p_step_desc)
            ]
        ]
        t_step = Table(s_card, colWidths=[18.6*cm])
        t_step.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), LIGHT if not s_prio else HexColor('#FBF2EE')),
            ('BOX', (0,0), (-1,-1), 0.5, RUST if s_prio else SAND),
            ('PADDING', (0,0), (-1,-1), 4),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
        ]))
        story.append(t_step)
        story.append(Spacer(1, 0.15*cm))

    # ── 20-Skill Complete Matrix ──
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph('Full 20-Skill Competency Assessment Matrix', p_sec))

    mat_data = [['Skill Name', 'Score', 'Status', 'Skill Name', 'Score', 'Status']]
    sorted_all = sorted(skill_profile.items()) if skill_profile else []
    for i in range(min(10, len(sorted_all))):
        k1, v1 = sorted_all[i]
        if i + 10 < len(sorted_all):
            k2, v2 = sorted_all[i+10]
        else:
            k2, v2 = ("", 0.0)
        st1 = 'Mastery' if float(v1) >= 8.0 else ('Proficient' if float(v1) >= 6.0 else ('Developing' if float(v1) >= 4.0 else 'Foundational'))
        st2 = 'Mastery' if float(v2) >= 8.0 else ('Proficient' if float(v2) >= 6.0 else ('Developing' if float(v2) >= 4.0 else 'Foundational')) if k2 else ""
        mat_data.append([
            k1, f'{float(v1):.1f}/10', st1,
            k2, f'{float(v2):.1f}/10' if k2 else "", st2
        ])

    t_mat = Table(mat_data, colWidths=[4.0*cm, 2.0*cm, 3.3*cm, 4.0*cm, 2.0*cm, 3.3*cm])
    t_mat.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), INK),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 7.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LIGHT]),
        ('GRID', (0,0), (-1,-1), 0.3, SAND),
        ('PADDING', (0,0), (-1,-1), 3),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
    ]))
    story.append(t_mat)

    # Footer notice
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width='100%', thickness=0.5, color=DUST, spaceAfter=3))
    story.append(Paragraph('<b>CareerLens Verification & Methodology</b>: Computed via 420 Mamdani fuzzy inference rules, Centroid Defuzzification, and Pearson shape correlation across 105 benchmark professions. Indicative guidance for academic and professional planning.', p_small))

    doc.build(story)
    buffer.seek(0)

    response = make_response(buffer.read())
    response.headers["Content-Type"] = "application/pdf"
    safe_name = "".join(c for c in (user["name"] if user else "user").replace(" ", "_") if c.isalnum() or c == "_")
    response.headers["Content-Disposition"] = f"attachment; filename={safe_name}_{user_id}_assessment{aid}.pdf"
    return response


@app.route("/api/pdf/<int:user_id>", methods=["GET"])
def generate_pdf(user_id):
    result = db.get_latest_result(user_id)
    if not result:
        return _err("No results found", 404)
    user = db.get_user_by_id(user_id)
    assessment_id = result.get("assessment_id", 0)
    return generate_pdf_response(result, user, assessment_id)


@app.route("/api/pdf/assessment/<int:assessment_id>", methods=["GET"])
def generate_pdf_by_assessment(assessment_id):
    result = db.get_results(assessment_id)
    if not result:
        return _err("No results found for this assessment", 404)
    row = db.connect().execute(
        "SELECT user_id FROM assessments WHERE id = ?", (assessment_id,)
    ).fetchone()
    user_id = row["user_id"] if row else None
    user = db.get_user_by_id(user_id) if user_id else None
    return generate_pdf_response(result, user, assessment_id)


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "db": str(DB_PATH)})


# ── evaluation routes ──────────────────────────────────────────────
EVAL_DIR = BASE.parent / "evaluation"
EVAL_DATA = BASE.parent / "data" / "evaluation"
FRONTEND_DIR = BASE.parent / "frontend"


@app.route("/api/evaluation/results", methods=["GET"])
def get_evaluation_results():
    """
    Returns the latest evaluation results JSON. If not yet generated,
    runs the evaluator against the default dataset automatically.
    """
    results_json = EVAL_DIR / "results.json"
    if results_json.exists():
        try:
            with open(results_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            return jsonify(data)
        except Exception as e:
            pass

    # Run evaluation if results.json not present
    try:
        sys.path.insert(0, str(EVAL_DIR))
        from evaluate_recommendations import RecommendationEvaluator, save_results
        evaluator = RecommendationEvaluator(data_dir=DATA)
        demo_path = EVAL_DATA / "ground_truth_demo.csv"
        real_path = EVAL_DATA / "ground_truth.csv"
        
        has_real = False
        if real_path.exists():
            with open(real_path, "r", encoding="utf-8") as f:
                lines = [l for l in f if l.strip() and not l.startswith("#")]
                if len(lines) > 1:
                    has_real = True
        target_path = real_path if has_real else demo_path
        results = evaluator.evaluate_all(target_path)
        save_results(results, EVAL_DIR)
        return jsonify(results)
    except Exception as err:
        return _err(f"Failed to run evaluation: {str(err)}", 500)


@app.route("/api/evaluation/run", methods=["POST"])
def run_evaluation_api():
    """
    Triggers a fresh evaluation run.
    Optional JSON body: { "dataset": "ground_truth_demo.csv" }
    """
    try:
        data = request.get_json(silent=True) or {}
        dataset_name = data.get("dataset", "ground_truth_demo.csv")
        target_path = EVAL_DATA / dataset_name
        if not target_path.exists():
            target_path = EVAL_DATA / "ground_truth_demo.csv"

        sys.path.insert(0, str(EVAL_DIR))
        from evaluate_recommendations import RecommendationEvaluator, save_results
        evaluator = RecommendationEvaluator(data_dir=DATA)
        results = evaluator.evaluate_all(target_path)
        save_results(results, EVAL_DIR)
        return jsonify(results)
    except Exception as err:
        return _err(f"Evaluation error: {str(err)}", 500)


@app.route("/api/evaluation/datasets", methods=["GET"])
def get_evaluation_datasets():
    """
    Returns metadata about available evaluation datasets.
    """
    datasets = []
    for f in [EVAL_DATA / "ground_truth.csv", EVAL_DATA / "ground_truth_demo.csv"]:
        if f.exists():
            with open(f, "r", encoding="utf-8") as file:
                lines = [l for l in file if l.strip() and not l.startswith("#")]
            row_count = max(0, len(lines) - 1)
            is_demo = "demo" in f.name.lower()
            datasets.append({
                "filename": f.name,
                "path": str(f),
                "is_synthetic": is_demo,
                "rows": row_count,
                "label": "Synthetic Benchmark Demo" if is_demo else "Real-World Cohort Data",
                "ready": row_count > 0
            })
    return jsonify({"datasets": datasets})


@app.route("/api/evaluation/download", methods=["GET"])
def download_evaluation_dataset():
    """
    Streams the benchmark ground truth dataset CSV as an attachment.
    """
    from flask import send_file
    target_path = EVAL_DATA / "ground_truth_demo.csv"
    if not target_path.exists():
        return _err("Benchmark dataset not found", 404)
    return send_file(
        str(target_path),
        mimetype="text/csv",
        as_attachment=True,
        download_name="CareerLens_Benchmark_GroundTruth_105Careers.csv"
    )


@app.route("/api/userdata/export", methods=["GET", "POST"])
def export_userdata_route():
    """
    Manually triggers regeneration of userdata CSVs and returns export summary.
    """
    try:
        res = export_userdata_to_csv(str(DB_PATH))
        return jsonify({"status": "success", "summary": res})
    except Exception as e:
        return _err(f"Export failed: {e}", 500)


@app.route("/api/userdata/csv", methods=["GET"])
def download_userdata_csv():
    """
    Streams the latest userdata.csv as an attachment.
    """
    from flask import send_file
    export_userdata_to_csv(str(DB_PATH))
    target_path = DATA.parent / "userdata" / "userdata.csv"
    if not target_path.exists():
        return _err("userdata.csv not found", 404)
    return send_file(
        str(target_path),
        mimetype="text/csv",
        as_attachment=True,
        download_name="userdata.csv"
    )


@app.route("/api/userdata/attempts/csv", methods=["GET"])
def download_user_attempts_csv():
    """
    Streams the detailed user_attempts.csv as an attachment.
    """
    from flask import send_file
    export_userdata_to_csv(str(DB_PATH))
    target_path = DATA.parent / "userdata" / "user_attempts.csv"
    if not target_path.exists():
        return _err("user_attempts.csv not found", 404)
    return send_file(
        str(target_path),
        mimetype="text/csv",
        as_attachment=True,
        download_name="user_attempts.csv"
    )


@app.route("/evaluation", methods=["GET"])
def serve_evaluation_page():
    """
    Serves the Evaluation Dashboard HTML.
    """
    from flask import send_from_directory
    return send_from_directory(str(FRONTEND_DIR), "evaluation.html")


@app.route("/", methods=["GET"])
def index():
    """
    Serves the main landing page.
    """
    from flask import send_from_directory
    return send_from_directory(str(FRONTEND_DIR), "index.html")


@app.route("/<path:path>", methods=["GET"])
def serve_frontend_assets(path):
    """
    Serves all frontend static assets, pages, styles, audio, and scripts.
    """
    from flask import send_from_directory
    file_path = FRONTEND_DIR / path
    if file_path.exists() and file_path.is_file():
        return send_from_directory(str(FRONTEND_DIR), path)
    if (FRONTEND_DIR / f"{path}.html").exists():
        return send_from_directory(str(FRONTEND_DIR), f"{path}.html")
    return send_from_directory(str(FRONTEND_DIR), "index.html")


# ── run ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    print(f"\nCareerLens web server running on port {port}")
    print(f"    DB  -> {DB_PATH}")
    print(f"    URL -> http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=False)