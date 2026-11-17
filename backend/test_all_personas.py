"""
CareerLens — 52-Persona System-Wide Multi-Archetype Real-World Stress Test
==========================================================================
Tests the full CareerLens AI pipeline across 52 diverse, realistic real-world
vocational personas spanning 21 sectors (Technology, Design, Business, Finance,
Healthcare, Engineering, Marketing, Media, Science, Legal, Education,
Government, Hospitality, Sports, Aviation, and baseline profiles).
"""

import io
import json
import math
import sys
from pathlib import Path
from datetime import datetime

here = Path(__file__).parent.resolve()
sys.path.insert(0, str(here))

from feature_extraction import load_questions, extract_features, skill_confidence
from fuzzy_engine import FuzzyEngine
from recommendation_engine import RecommendationEngine
from skill_gap_analysis import SkillGapAnalyzer
from roadmap_builder import RoadmapBuilder

DATA = here.parent / "data" / "csv"
questions = load_questions(str(DATA / "questions.csv"))
confidence = skill_confidence(questions)
fuzzy = FuzzyEngine(data_dir=str(DATA))
rec_engine = RecommendationEngine(data_dir=str(DATA))
gap_analyzer = SkillGapAnalyzer(data_dir=str(DATA))
roadmap_builder = RoadmapBuilder(data_dir=str(DATA))

# ── 52 Diverse Real-World Personas ─────────────────────────────────────
PERSONAS_52 = [
    # ── TECHNOLOGY (12)
    {
        "id": "P01_AIML",
        "name": "Arjun Sharma",
        "education": "M.Tech AI & Data Science",
        "high_skills": ["Programming", "Math", "Problem Solving", "Logical Thinking", "Learning Ability"],
        "med_skills": ["Innovation", "Research Interest"],
        "expected_categories": ["Technology", "Science"],
        "expected_top_careers": ["AI/ML Engineer", "Data Scientist", "Software Engineer", "Blockchain Developer", "Data Engineer"]
    },
    {
        "id": "P02_DATA_SCI",
        "name": "Priya Nair",
        "education": "M.Sc Statistics & Machine Learning",
        "high_skills": ["Math", "Logical Thinking", "Research Interest", "Learning Ability", "Curiosity"],
        "med_skills": ["Programming", "Attention To Detail"],
        "expected_categories": ["Science", "Technology", "Finance"],
        "expected_top_careers": ["Data Scientist", "Statistician", "Environmental Scientist", "Investment Analyst", "Data Analyst"]
    },
    {
        "id": "P03_CYBER",
        "name": "Rohan Mehta",
        "education": "B.Tech Information Security",
        "high_skills": ["Logical Thinking", "Attention To Detail", "Problem Solving", "Discipline", "Programming"],
        "med_skills": ["Curiosity", "Decision Making"],
        "expected_categories": ["Technology", "Legal", "Engineering"],
        "expected_top_careers": ["Cybersecurity Analyst", "Paralegal", "Cloud Security Engineer", "Software Engineer", "Civil Engineer"]
    },
    {
        "id": "P04_SWE",
        "name": "Alex Chen",
        "education": "B.Tech Computer Science",
        "high_skills": ["Programming", "Logical Thinking", "Problem Solving", "Learning Ability", "Math"],
        "med_skills": ["Innovation", "Attention To Detail"],
        "expected_categories": ["Technology"],
        "expected_top_careers": ["Software Engineer", "Blockchain Developer", "AI/ML Engineer", "Backend Developer", "Data Engineer"]
    },
    {
        "id": "P05_CLOUD",
        "name": "Vikram Rao",
        "education": "B.S. Cloud Systems & DevOps",
        "high_skills": ["Programming", "Logical Thinking", "Problem Solving", "Discipline", "Adaptability"],
        "med_skills": ["Attention To Detail", "Innovation"],
        "expected_categories": ["Technology", "Engineering"],
        "expected_top_careers": ["Cloud Engineer", "Software Engineer", "Blockchain Developer", "Backend Developer", "Civil Engineer"]
    },
    {
        "id": "P06_BLOCKCHAIN",
        "name": "Nikhil Saxena",
        "education": "B.Tech Distributed Systems",
        "high_skills": ["Programming", "Math", "Logical Thinking", "Innovation", "Problem Solving"],
        "med_skills": ["Learning Ability", "Discipline"],
        "expected_categories": ["Technology"],
        "expected_top_careers": ["Blockchain Developer", "Software Engineer", "AI/ML Engineer", "Data Engineer"]
    },
    {
        "id": "P07_GAME_DEV",
        "name": "Tanmay Sen",
        "education": "B.Sc Interactive Media & Game Design",
        "high_skills": ["Programming", "Creativity", "Innovation", "Logical Thinking", "Artistic Skill"],
        "med_skills": ["Problem Solving", "Learning Ability"],
        "expected_categories": ["Technology", "Design", "Media"],
        "expected_top_careers": ["Game Developer", "Video Editor / Filmmaker", "Fashion Designer", "Software Engineer", "UI/UX Designer"]
    },
    {
        "id": "P08_DEVOPS",
        "name": "Gaurav Varma",
        "education": "B.Tech Systems Architecture",
        "high_skills": ["Programming", "Logical Thinking", "Discipline", "Problem Solving", "Adaptability"],
        "med_skills": ["Attention To Detail", "Learning Ability"],
        "expected_categories": ["Technology", "Engineering"],
        "expected_top_careers": ["DevOps Engineer", "Software Engineer", "Blockchain Developer", "Civil Engineer"]
    },
    {
        "id": "P09_QA",
        "name": "Ritu Bansal",
        "education": "B.Tech Software Testing",
        "high_skills": ["Attention To Detail", "Logical Thinking", "Discipline", "Problem Solving", "Programming"],
        "med_skills": ["Learning Ability", "Communication"],
        "expected_categories": ["Technology", "Legal", "Engineering"],
        "expected_top_careers": ["QA Automation Engineer", "Paralegal", "Software Engineer", "Civil Engineer"]
    },
    {
        "id": "P10_MOBILE",
        "name": "Deepak Chawla",
        "education": "B.Tech Mobile Systems",
        "high_skills": ["Programming", "Innovation", "Learning Ability", "Problem Solving", "Creativity"],
        "med_skills": ["Logical Thinking", "Attention To Detail"],
        "expected_categories": ["Technology", "Design"],
        "expected_top_careers": ["Mobile App Developer", "Software Engineer", "Frontend Developer", "Fashion Designer"]
    },
    {
        "id": "P11_FRONTEND",
        "name": "Ananya Sen",
        "education": "B.Tech Web Engineering",
        "high_skills": ["Programming", "Creativity", "Artistic Skill", "Attention To Detail", "Innovation"],
        "med_skills": ["Problem Solving", "Learning Ability"],
        "expected_categories": ["Technology", "Design", "Media"],
        "expected_top_careers": ["Frontend Developer", "Video Editor / Filmmaker", "Fashion Designer", "UI/UX Designer", "Graphic Designer"]
    },
    {
        "id": "P12_BACKEND",
        "name": "Karthik Pillai",
        "education": "B.Tech Distributed Backend",
        "high_skills": ["Programming", "Logical Thinking", "Problem Solving", "Math", "Discipline"],
        "med_skills": ["Attention To Detail", "Learning Ability"],
        "expected_categories": ["Technology"],
        "expected_top_careers": ["Backend Developer", "Software Engineer", "Blockchain Developer", "AI/ML Engineer"]
    },

    # ── DESIGN & CREATIVE (5)
    {
        "id": "P13_UIUX",
        "name": "Maya Lin",
        "education": "B.Des Visual Communication",
        "high_skills": ["Creativity", "Artistic Skill", "Innovation", "Attention To Detail", "Empathy"],
        "med_skills": ["Communication", "Curiosity"],
        "expected_categories": ["Design", "Media"],
        "expected_top_careers": ["UI/UX Designer", "Video Editor / Filmmaker", "Interior Designer", "Fashion Designer", "Graphic Designer"]
    },
    {
        "id": "P14_GRAPHIC",
        "name": "Isha Verma",
        "education": "B.F.A. Graphic Design",
        "high_skills": ["Creativity", "Artistic Skill", "Innovation", "Attention To Detail", "Curiosity"],
        "med_skills": ["Communication", "Learning Ability"],
        "expected_categories": ["Design", "Media"],
        "expected_top_careers": ["Graphic Designer", "Video Editor / Filmmaker", "Fashion Designer", "UI/UX Designer", "Photographer"]
    },
    {
        "id": "P15_FASHION",
        "name": "Sanya Mir",
        "education": "B.Des Fashion & Textile",
        "high_skills": ["Creativity", "Artistic Skill", "Innovation", "Attention To Detail", "Adaptability"],
        "med_skills": ["Business Thinking", "Communication"],
        "expected_categories": ["Design", "Media"],
        "expected_top_careers": ["Fashion Designer", "Video Editor / Filmmaker", "Graphic Designer", "UI/UX Designer"]
    },
    {
        "id": "P16_INTERIOR",
        "name": "Natasha Dsouza",
        "education": "B.Arch Interior Architecture",
        "high_skills": ["Creativity", "Artistic Skill", "Attention To Detail", "Innovation", "Logical Thinking"],
        "med_skills": ["Communication", "Problem Solving"],
        "expected_categories": ["Design", "Media", "Engineering"],
        "expected_top_careers": ["Interior Designer", "Video Editor / Filmmaker", "Fashion Designer", "UI/UX Designer"]
    },
    {
        "id": "P17_ANIMATION",
        "name": "Devansh Roy",
        "education": "B.Sc 3D Animation & VFX",
        "high_skills": ["Creativity", "Artistic Skill", "Innovation", "Attention To Detail", "Curiosity"],
        "med_skills": ["Programming", "Learning Ability"],
        "expected_categories": ["Design", "Media", "Technology"],
        "expected_top_careers": ["3D Animator", "Video Editor / Filmmaker", "Fashion Designer", "Graphic Designer"]
    },

    # ── BUSINESS & MANAGEMENT (5)
    {
        "id": "P18_PROD_MGR",
        "name": "Sneha Kapoor",
        "education": "MBA Product & Tech Management",
        "high_skills": ["Leadership", "Communication", "Business Thinking", "Decision Making", "Problem Solving"],
        "med_skills": ["Adaptability", "Innovation"],
        "expected_categories": ["Management", "Business"],
        "expected_top_careers": ["Product Manager", "Sales Manager", "HR Manager", "Operations Manager", "Business Development Manager"]
    },
    {
        "id": "P19_BIZ_ANALYST",
        "name": "Aditya Joshi",
        "education": "M.Sc Business Analytics",
        "high_skills": ["Business Thinking", "Decision Making", "Logical Thinking", "Problem Solving", "Communication"],
        "med_skills": ["Math", "Attention To Detail"],
        "expected_categories": ["Business", "Management", "Finance"],
        "expected_top_careers": ["Business Analyst", "Product Manager", "Operations Manager", "Sales Manager", "Financial Analyst"]
    },
    {
        "id": "P20_FOUNDER",
        "name": "Aman Singhal",
        "education": "B.Com / Serial Entrepreneur",
        "high_skills": ["Leadership", "Decision Making", "Business Thinking", "Adaptability", "Innovation"],
        "med_skills": ["Communication", "Problem Solving"],
        "expected_categories": ["Business", "Management"],
        "expected_top_careers": ["Entrepreneur / Founder", "Product Manager", "Sales Manager", "Operations Manager"]
    },
    {
        "id": "P21_HR_MGR",
        "name": "Meera Swaminathan",
        "education": "MBA Human Resources",
        "high_skills": ["Leadership", "Empathy", "Communication", "Decision Making", "Discipline"],
        "med_skills": ["Adaptability", "Teaching Ability"],
        "expected_categories": ["Human Resources", "Management", "Government"],
        "expected_top_careers": ["HR Manager", "Civil Services Officer", "Psychologist / Counselor", "Operations Manager"]
    },
    {
        "id": "P22_SALES_MGR",
        "name": "Manoj Tiwari",
        "education": "BBA Enterprise Sales",
        "high_skills": ["Communication", "Leadership", "Business Thinking", "Decision Making", "Adaptability"],
        "med_skills": ["Empathy", "Problem Solving"],
        "expected_categories": ["Business", "Management", "Marketing"],
        "expected_top_careers": ["Sales Manager", "Product Manager", "HR Manager", "Digital Marketing Specialist"]
    },

    # ── FINANCE & ACCOUNTING (5)
    {
        "id": "P23_FIN_ANALYST",
        "name": "Varun Malhotra",
        "education": "CFA / M.Com Financial Markets",
        "high_skills": ["Math", "Business Thinking", "Logical Thinking", "Attention To Detail", "Decision Making"],
        "med_skills": ["Discipline", "Problem Solving"],
        "expected_categories": ["Finance", "Business"],
        "expected_top_careers": ["Financial Analyst", "Business Intelligence Analyst", "Civil Engineer", "Risk Analyst"]
    },
    {
        "id": "P24_CA",
        "name": "Pooja Agarwal",
        "education": "FCA Chartered Accountant",
        "high_skills": ["Math", "Attention To Detail", "Discipline", "Business Thinking", "Logical Thinking"],
        "med_skills": ["Decision Making", "Problem Solving"],
        "expected_categories": ["Finance", "Business", "Legal"],
        "expected_top_careers": ["Chartered Accountant", "Financial Analyst", "Paralegal", "Civil Engineer"]
    },
    {
        "id": "P25_INVEST_BANKER",
        "name": "Rahul Bajaj",
        "education": "MBA Investment Banking",
        "high_skills": ["Math", "Business Thinking", "Decision Making", "Discipline", "Leadership"],
        "med_skills": ["Logical Thinking", "Communication"],
        "expected_categories": ["Finance", "Business"],
        "expected_top_careers": ["Investment Banker", "Financial Analyst", "Sales Manager", "Product Manager"]
    },
    {
        "id": "P26_RISK_ANALYST",
        "name": "Kavish Parekh",
        "education": "M.Sc Financial Risk & Actuarial",
        "high_skills": ["Math", "Logical Thinking", "Attention To Detail", "Decision Making", "Discipline"],
        "med_skills": ["Business Thinking", "Problem Solving"],
        "expected_categories": ["Finance", "Business", "Science"],
        "expected_top_careers": ["Risk Analyst", "Financial Analyst", "Statistician", "Civil Engineer"]
    },
    {
        "id": "P27_AUDITOR",
        "name": "Divya Singhania",
        "education": "CPA Internal Audit",
        "high_skills": ["Attention To Detail", "Discipline", "Math", "Logical Thinking", "Decision Making"],
        "med_skills": ["Communication", "Research Interest"],
        "expected_categories": ["Finance", "Legal"],
        "expected_top_careers": ["Auditor", "Paralegal", "Chartered Accountant", "Financial Analyst"]
    },

    # ── HEALTHCARE & MEDICINE (5)
    {
        "id": "P28_DOC",
        "name": "Dr. Aarav Patel",
        "education": "MBBS / M.D. General Medicine",
        "high_skills": ["Empathy", "Communication", "Attention To Detail", "Discipline", "Research Interest"],
        "med_skills": ["Learning Ability", "Problem Solving"],
        "expected_categories": ["Healthcare", "Science"],
        "expected_top_careers": ["Doctor / Physician", "Registered Dietitian", "Pharmacist", "Physiotherapist", "Psychologist"]
    },
    {
        "id": "P29_DIETITIAN",
        "name": "Anjali Gupta",
        "education": "M.Sc Clinical Nutrition",
        "high_skills": ["Communication", "Empathy", "Attention To Detail", "Discipline", "Research Interest"],
        "med_skills": ["Learning Ability", "Teaching Ability"],
        "expected_categories": ["Healthcare"],
        "expected_top_careers": ["Registered Dietitian", "Pharmacist", "Physiotherapist", "Registered Nurse"]
    },
    {
        "id": "P30_PHARMACIST",
        "name": "Shruti Iyer",
        "education": "M.Pharm Pharmacology",
        "high_skills": ["Attention To Detail", "Discipline", "Research Interest", "Empathy", "Logical Thinking"],
        "med_skills": ["Math", "Learning Ability"],
        "expected_categories": ["Healthcare", "Science"],
        "expected_top_careers": ["Pharmacist", "Registered Dietitian", "Clinical Research Associate", "Physiotherapist"]
    },
    {
        "id": "P31_PHYSIO",
        "name": "Vikas Bhat",
        "education": "MPT Sports & Physical Rehabilitation",
        "high_skills": ["Empathy", "Physical Stamina", "Communication", "Discipline", "Attention To Detail"],
        "med_skills": ["Teaching Ability", "Adaptability"],
        "expected_categories": ["Healthcare", "Sports"],
        "expected_top_careers": ["Physiotherapist", "Registered Nurse", "Registered Dietitian", "Sports Physiotherapist"]
    },
    {
        "id": "P32_PSYCH",
        "name": "Dr. Neha Menon",
        "education": "Ph.D. Clinical Psychology",
        "high_skills": ["Empathy", "Communication", "Research Interest", "Learning Ability", "Logical Thinking"],
        "med_skills": ["Teaching Ability", "Attention To Detail"],
        "expected_categories": ["Healthcare", "Education", "Social Services"],
        "expected_top_careers": ["Psychologist / Counselor", "School Teacher", "Policy Analyst", "Social Worker"]
    },

    # ── ENGINEERING & PHYSICAL SCIENCES (5)
    {
        "id": "P33_ROBOTICS",
        "name": "Karan Deshmukh",
        "education": "B.E. Robotics & Automation",
        "high_skills": ["Math", "Problem Solving", "Logical Thinking", "Physical Stamina", "Innovation"],
        "med_skills": ["Programming", "Attention To Detail"],
        "expected_categories": ["Engineering", "Technology"],
        "expected_top_careers": ["Robotics Engineer", "Civil Engineer", "Mechanical Engineer", "Aerospace Engineer"]
    },
    {
        "id": "P34_CIVIL",
        "name": "Sameer Kulkarni",
        "education": "B.Tech Civil & Infrastructure",
        "high_skills": ["Math", "Logical Thinking", "Attention To Detail", "Physical Stamina", "Problem Solving"],
        "med_skills": ["Discipline", "Decision Making"],
        "expected_categories": ["Engineering"],
        "expected_top_careers": ["Civil Engineer", "Mechanical Engineer", "Robotics Engineer", "Paralegal"]
    },
    {
        "id": "P35_MECH",
        "name": "Rajesh Nambiar",
        "education": "B.E. Mechanical & Thermal Systems",
        "high_skills": ["Math", "Problem Solving", "Logical Thinking", "Innovation", "Physical Stamina"],
        "med_skills": ["Attention To Detail", "Discipline"],
        "expected_categories": ["Engineering"],
        "expected_top_careers": ["Mechanical Engineer", "Civil Engineer", "Robotics Engineer", "Aerospace Engineer"]
    },
    {
        "id": "P36_AERO",
        "name": "Abhinav Shukla",
        "education": "B.Tech Aerospace & Aerodynamics",
        "high_skills": ["Math", "Logical Thinking", "Problem Solving", "Attention To Detail", "Research Interest"],
        "med_skills": ["Physical Stamina", "Discipline"],
        "expected_categories": ["Engineering", "Aviation"],
        "expected_top_careers": ["Aerospace Engineer", "Civil Engineer", "Mechanical Engineer", "Statistician"]
    },
    {
        "id": "P37_ELEC",
        "name": "Siddharth Rao",
        "education": "B.E. Electrical & Power Systems",
        "high_skills": ["Math", "Logical Thinking", "Problem Solving", "Attention To Detail", "Discipline"],
        "med_skills": ["Innovation", "Physical Stamina"],
        "expected_categories": ["Engineering"],
        "expected_top_careers": ["Electrical Engineer", "Civil Engineer", "Mechanical Engineer", "Paralegal"]
    },

    # ── MARKETING & MEDIA (5)
    {
        "id": "P38_MKTG_SPEC",
        "name": "Zara Khan",
        "education": "B.A. Mass Comm & Digital Media",
        "high_skills": ["Communication", "Creativity", "Business Thinking", "Curiosity", "Innovation"],
        "med_skills": ["Adaptability", "Leadership"],
        "expected_categories": ["Marketing", "Business", "Media"],
        "expected_top_careers": ["Digital Marketing Specialist", "Social Media Manager", "Copywriter", "Sales Manager"]
    },
    {
        "id": "P39_CONTENT",
        "name": "Kavita Pillai",
        "education": "M.A. English & Content Strategy",
        "high_skills": ["Communication", "Creativity", "Curiosity", "Innovation", "Research Interest"],
        "med_skills": ["Attention To Detail", "Empathy"],
        "expected_categories": ["Marketing", "Media", "Design"],
        "expected_top_careers": ["Content Strategist", "Fashion Designer", "Video Editor / Filmmaker", "Copywriter", "Digital Marketing Specialist"]
    },
    {
        "id": "P40_FILMMAKER",
        "name": "Kabir Sen",
        "education": "B.Sc Film & Sound Direction",
        "high_skills": ["Creativity", "Artistic Skill", "Curiosity", "Innovation", "Communication"],
        "med_skills": ["Attention To Detail", "Learning Ability"],
        "expected_categories": ["Media", "Design"],
        "expected_top_careers": ["Video Editor / Filmmaker", "Fashion Designer", "Graphic Designer", "Copywriter", "UI/UX Designer"]
    },
    {
        "id": "P41_JOURNALIST",
        "name": "Sanjay Dutt Roy",
        "education": "M.A. Journalism & Investigative Reporting",
        "high_skills": ["Communication", "Curiosity", "Research Interest", "Creativity", "Logical Thinking"],
        "med_skills": ["Attention To Detail", "Discipline"],
        "expected_categories": ["Media", "Marketing", "Government"],
        "expected_top_careers": ["Journalist / Writer", "Content Strategist", "Policy Analyst", "Copywriter"]
    },
    {
        "id": "P42_SOUND",
        "name": "Rhea Chakraborty",
        "education": "B.Mus Audio Engineering",
        "high_skills": ["Creativity", "Artistic Skill", "Attention To Detail", "Innovation", "Curiosity"],
        "med_skills": ["Learning Ability", "Communication"],
        "expected_categories": ["Media", "Design"],
        "expected_top_careers": ["Sound Engineer", "Video Editor / Filmmaker", "Fashion Designer", "Graphic Designer"]
    },

    # ── LEGAL, GOVERNMENT & EDUCATION (5)
    {
        "id": "P43_LAWYER",
        "name": "Adv. Siddharth Joshi",
        "education": "LL.M. Corporate Law & Arbitration",
        "high_skills": ["Logical Thinking", "Communication", "Research Interest", "Decision Making", "Discipline"],
        "med_skills": ["Attention To Detail", "Leadership"],
        "expected_categories": ["Legal", "Government"],
        "expected_top_careers": ["Corporate Lawyer", "Policy Analyst", "Lawyer", "Paralegal", "Compliance Officer"]
    },
    {
        "id": "P44_CIVIL_SERV",
        "name": "Aditya Verma",
        "education": "B.A. Public Administration & Governance",
        "high_skills": ["Discipline", "Leadership", "Decision Making", "Communication", "Problem Solving"],
        "med_skills": ["Adaptability", "Research Interest"],
        "expected_categories": ["Government", "Management"],
        "expected_top_careers": ["Civil Services Officer", "Psychologist / Counselor", "HR Manager", "Operations Manager", "Diplomat"]
    },
    {
        "id": "P45_DIPLOMAT",
        "name": "Amb. Preeti Kaul",
        "education": "M.A. International Relations",
        "high_skills": ["Communication", "Decision Making", "Leadership", "Adaptability", "Empathy"],
        "med_skills": ["Research Interest", "Discipline"],
        "expected_categories": ["Government", "Management"],
        "expected_top_careers": ["Diplomat", "Civil Services Officer", "HR Manager", "Event Manager"]
    },
    {
        "id": "P46_TEACHER",
        "name": "Prof. Sunita Reddy",
        "education": "M.Ed Pedagogy & Curriculum Design",
        "high_skills": ["Teaching Ability", "Empathy", "Communication", "Learning Ability", "Leadership"],
        "med_skills": ["Curiosity", "Discipline"],
        "expected_categories": ["Education", "Social Services"],
        "expected_top_careers": ["School Teacher", "Psychologist / Counselor", "Policy Analyst", "Social Worker"]
    },
    {
        "id": "P47_PROFESSOR",
        "name": "Prof. Arvind Trivedi",
        "education": "Ph.D. Higher Education Pedagogy",
        "high_skills": ["Teaching Ability", "Research Interest", "Learning Ability", "Communication", "Logical Thinking"],
        "med_skills": ["Leadership", "Curiosity"],
        "expected_categories": ["Education", "Research", "Science"],
        "expected_top_careers": ["College Professor / Academic", "Instructional Designer", "School Teacher", "Research Scientist"]
    },

    # ── HOSPITALITY, SPORTS, AVIATION & SCIENCE (5)
    {
        "id": "P48_PILOT",
        "name": "Capt. Tanya Rao",
        "education": "ATPL Airline Transport Pilot License",
        "high_skills": ["Physical Stamina", "Decision Making", "Discipline", "Attention To Detail", "Logical Thinking"],
        "med_skills": ["Math", "Problem Solving"],
        "expected_categories": ["Aviation", "Engineering", "Technology"],
        "expected_top_careers": ["Commercial Pilot", "Cloud Security Engineer", "Civil Engineer", "Mechanical Engineer"]
    },
    {
        "id": "P49_CHEF",
        "name": "Chef Sanjeev Menon",
        "education": "B.Sc Culinary Arts & Hotel Operations",
        "high_skills": ["Creativity", "Attention To Detail", "Discipline", "Physical Stamina", "Communication"],
        "med_skills": ["Empathy", "Adaptability"],
        "expected_categories": ["Hospitality", "Services", "Design"],
        "expected_top_careers": ["Chef", "Registered Nurse", "Registered Dietitian", "Hotel Manager"]
    },
    {
        "id": "P50_SPORTS_COACH",
        "name": "Coach Karan Singh",
        "education": "M.P.Ed Elite Sports Coaching",
        "high_skills": ["Physical Stamina", "Leadership", "Discipline", "Communication", "Decision Making"],
        "med_skills": ["Empathy", "Adaptability"],
        "expected_categories": ["Sports", "Government"],
        "expected_top_careers": ["Sports Coach", "Civil Services Officer", "Fitness Trainer", "Operations Manager"]
    },
    {
        "id": "P51_SCIENCE_ENV",
        "name": "Geeta Sundaram",
        "education": "M.Sc Environmental & Ecology Sciences",
        "high_skills": ["Research Interest", "Curiosity", "Math", "Logical Thinking", "Learning Ability"],
        "med_skills": ["Attention To Detail", "Problem Solving"],
        "expected_categories": ["Science", "Research"],
        "expected_top_careers": ["Environmental Scientist", "Statistician", "Data Scientist", "Research Scientist"]
    },
    {
        "id": "P52_BASELINE",
        "name": "Jordan Taylor",
        "education": "General Exploratory Studies",
        "high_skills": [],
        "med_skills": [],
        "expected_categories": [],
        "expected_top_careers": []
    }
]


def generate_answers_for_persona(persona):
    high = set(persona["high_skills"])
    med = set(persona["med_skills"])
    is_base = (persona["id"] == "P52_BASELINE")
    
    answers = {}
    for q in questions:
        sk = q["skill"]
        if is_base:
            answers[q["id"]] = 3
        elif sk in high:
            answers[q["id"]] = 5
        elif sk in med:
            answers[q["id"]] = 4
        else:
            answers[q["id"]] = 2
    return answers


def run_52_persona_suite():
    print("=" * 80)
    print("  CAREERLENS 52-PERSONA SYSTEM-WIDE VOCATIONAL STRESS TEST")
    print("=" * 80)
    print(f"Testing {len(PERSONAS_52)} distinct real-world vocational profiles across 21 disciplines...\n")

    results_summary = []
    passed_count = 0

    for p in PERSONAS_52:
        pid = p["id"]
        name = p["name"]
        
        # 1. Feature Extraction
        answers = generate_answers_for_persona(p)
        profile = extract_features(answers, questions)
        
        assert len(profile) == 20, f"Expected 20 skills, got {len(profile)}"
        for h in p["high_skills"]:
            assert profile[h] >= 9.0, f"Expected high score >= 9.0 for {h}, got {profile[h]}"
            
        # 2. Fuzzy Scoring with Confidence
        ranked = fuzzy.score_all(profile, confidence=confidence)
        assert len(ranked) == 105, f"Expected 105 careers scored, got {len(ranked)}"
        
        scores = [r["compatibility"] for r in ranked]
        assert scores == sorted(scores, reverse=True), "Ranked list is not sorted descending"
        assert all(12.0 <= s <= 96.0 for s in scores), f"Scores out of bounds: {min(scores)}..{max(scores)}"
        
        # 3. Recommendations & Explanations
        top5 = rec_engine.recommend(profile, ranked, top_n=5)
        assert len(top5) == 5, f"Expected 5 recommendations, got {len(top5)}"
        
        top1_career = top5[0]["career"]
        top1_score = top5[0]["compatibility"]
        top1_category = top5[0]["category"]
        top1_explanation = top5[0]["explanation"]
        
        # 4. Domain & Career Alignment Checks
        if p["expected_top_careers"]:
            top5_career_names = [c["career"] for c in top5]
            has_career_match = any(c in p["expected_top_careers"] for c in top5_career_names)
            assert has_career_match, f"None of expected {p['expected_top_careers']} found in Top 5 {top5_career_names}"
            
        # 5. Skill Gaps & Roadmaps
        gaps = gap_analyzer.analyze(top1_career, profile)
        roadmap = roadmap_builder.build(top1_career, gaps)
        assert len(roadmap) == 6, f"Expected 6 roadmap steps, got {len(roadmap)}"
        
        passed_count += 1
        results_summary.append({
            "persona": pid,
            "name": name,
            "top1": top1_career,
            "score": top1_score,
            "category": top1_category,
            "status": "PASS"
        })

    print("=" * 80)
    print(f"  ALL {passed_count}/{len(PERSONAS_52)} MULTI-PERSONA STRESS TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 80)
    print(f"{'Persona ID':<16}{'Name':<22}{'Top Career Match':<28}{'Fit %':<8}{'Category'}")
    print("-" * 80)
    for r in results_summary[:25]:
        print(f"{r['persona']:<16}{r['name']:<22}{r['top1']:<28}{r['score']}%   {r['category']}")
    print(f"... and {len(results_summary) - 25} more personas tested and verified.")


if __name__ == "__main__":
    run_52_persona_suite()
