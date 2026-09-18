"""
Add Sheet 6: Feasibility & ROI Analysis
For every gap from Sheet 5, estimate:
  - Effort (Low/Medium/High/Very High) + concrete hours
  - Compute (GPU-hours needed)
  - Data source (specific scrape URLs / APIs)
  - Labeling required? (Yes/No, # annotators, expertise level)
  - Annotation time
  - Total calendar time
  - Target journal/venue (CCF-A / Q1 / SCI)
  - ROI score (1-10) — low effort + high impact = high ROI
  - Why publishable
"""

import sys, os
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font, Border, Side, Alignment
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import CellIsRule, FormulaRule, ColorScaleRule

sys.path.insert(0, "/home/z/my-project/scripts")
from papers_data import PAPERS

# Design tokens
PRIMARY = "1F4E79"
ACCENT = "C00000"
SUCCESS = "2E7D32"
WARNING = "ED6C02"
DANGER = "C62828"
LIGHT_BG = "F4F6F9"
ALT_ROW = "FAFBFC"
HEADER_BG = "1F4E79"
HEADER_FG = "FFFFFF"
KPI_BG = "E8F1FA"
GAP_CRITICAL = "FCE4E4"
GAP_HIGH = "FFF4E4"
GAP_NONE = "E8F5E9"
GAP_MEDIUM = "FFF9C4"
FONT_NAME = "Calibri"

def thin_border():
    side = Side(style="thin", color="D0D7E2")
    return Border(left=side, right=side, top=side, bottom=side)

def header_style():
    return {
        "fill": PatternFill("solid", fgColor=HEADER_BG),
        "font": Font(name=FONT_NAME, size=11, bold=True, color=HEADER_FG),
        "alignment": Alignment(horizontal="center", vertical="center", wrap_text=True),
        "border": thin_border(),
    }

def body_style(bold=False, color="000000", bg=None, align="left", size=10):
    s = {
        "font": Font(name=FONT_NAME, size=size, bold=bold, color=color),
        "alignment": Alignment(horizontal=align, vertical="center", wrap_text=True),
        "border": thin_border(),
    }
    if bg:
        s["fill"] = PatternFill("solid", fgColor=bg)
    return s

def apply_style(cell, style):
    for k, v in style.items():
        setattr(cell, k, v)

# ============================================================
# FEASIBILITY DATA — Each entry is a gap to fill
# ============================================================
# (task, effort_level, effort_hours, compute_level, gpu_hours, data_source,
#  labeling_reqd, num_annotators, expertise, annotation_weeks, total_weeks,
#  target_venue, roi_score, why_publishable, easy_wins_tag)
#
# ROI = (Impact * Publication Potential) / (Effort * Compute * Labeling)
# 10 = absolute easy win, 1 = brutal grind

FEASIBILITY = [
    # ===== EASY WINS (ROI 8-10) — High impact, low effort, minimal labeling =====
    {
        "task": "Translate COMET-ATOMIC to Urdu (Commonsense Reasoning)",
        "category": "Zero-work",
        "effort_level": "Low",
        "effort_hours": "60-80 hrs",
        "compute_level": "Low",
        "gpu_hours": "20-50 (A100 hrs for fine-tuning)",
        "data_source": "COMET-ATOMIC 2024 (https://github.com/allenai/comet_atomic2020) — translate via GPT-4o then human-post-edit 5%",
        "labeling": "Yes (post-editing only)",
        "annotators": "2-3 native Urdu speakers (students OK)",
        "expertise": "Student annotators",
        "annotation_weeks": "2-3 weeks",
        "total_weeks": "6-8 weeks",
        "target_venue": "ACL Findings / EMNLP Findings (CCF-A)",
        "roi_score": 9,
        "why_publishable": "First Urdu commonsense KB — guaranteed novelty; COMET-ATOMIC is widely cited; cross-lingual commonsense is hot topic",
        "easy_win": "Yes — top 5 easy win",
    },
    {
        "task": "Build UrduSpider (Text-to-SQL)",
        "category": "Zero-work",
        "effort_level": "Low",
        "effort_hours": "80-100 hrs",
        "compute_level": "Low",
        "gpu_hours": "30-50 (T5/mT5 fine-tune)",
        "data_source": "Spider benchmark (https://yale-lily.github.io/spider) — translate questions + schema via LLM, post-edit critical 10%",
        "labeling": "Yes (SQL validation)",
        "annotators": "1-2 CS students with SQL skills",
        "expertise": "CS students",
        "annotation_weeks": "3-4 weeks",
        "total_weeks": "8-10 weeks",
        "target_venue": "NAACL / ACL Findings (CCF-A)",
        "roi_score": 9,
        "why_publishable": "First Urdu text-to-SQL — high practical value for local software industry; Spider is benchmark-of-choice",
        "easy_win": "Yes — top 5 easy win",
    },
    {
        "task": "Translate DROP to Urdu (Numerical Reasoning)",
        "category": "Zero-work",
        "effort_level": "Low",
        "effort_hours": "50-70 hrs",
        "compute_level": "Low",
        "gpu_hours": "20-40 (fine-tune mT5)",
        "data_source": "DROP (https://allennlp.org/drop) — translate via LLM, post-edit numerical answers (numbers stay same)",
        "labeling": "Yes (minimal — answer validation)",
        "annotators": "2 students",
        "expertise": "Students",
        "annotation_weeks": "2 weeks",
        "total_weeks": "5-6 weeks",
        "target_venue": "ACL Findings / EMNLP Findings (CCF-A)",
        "roi_score": 9,
        "why_publishable": "First Urdu numerical reasoning benchmark — fills obvious gap; DROP is well-known",
        "easy_win": "Yes — top 5 easy win",
    },
    {
        "task": "Build Urdu-SemEval ABSA (Aspect-based Sentiment, large)",
        "category": "Tiny-dataset",
        "effort_level": "Low-Medium",
        "effort_hours": "100-150 hrs",
        "compute_level": "Low",
        "gpu_hours": "30-60 (BERT fine-tune)",
        "data_source": "Scrape Daraz.pk reviews + Yelp-style Urdu reviews from Google Play Store Urdu apps; SemEval-2014 ABSA schema",
        "labeling": "Yes (aspect + polarity)",
        "annotators": "3-4 students",
        "expertise": "Students with light training",
        "annotation_weeks": "4-5 weeks",
        "total_weeks": "8-10 weeks",
        "target_venue": "NAACL / LREC-COLING (CCF-B) → Knowledge-Based Systems (Q1 SCI)",
        "roi_score": 8,
        "why_publishable": "Current Urdu ABSA is only 2k reviews — too small; SemEval-style benchmark easily publishable",
        "easy_win": "Yes — top 10 easy win",
    },
    {
        "task": "Urdu Multi-domain Sentiment (50k+)",
        "category": "Tiny-dataset",
        "effort_level": "Low",
        "effort_hours": "60-80 hrs",
        "compute_level": "Low",
        "gpu_hours": "20-30",
        "data_source": "Scrape Daraz.pk (products), Foodpanda.pk (restaurants), Bookmeter.pk, Google Play Urdu app reviews, YouTube Urdu comments via yt-dlp",
        "labeling": "Yes (3-class sentiment)",
        "annotators": "3 students",
        "expertise": "Students",
        "annotation_weeks": "3 weeks",
        "total_weeks": "6-8 weeks",
        "target_venue": "IEEE Access (Q1 SCI, easy acceptance) / PLOS ONE",
        "roi_score": 8,
        "why_publishable": "UrduSent is 10k tweets only — multi-domain is publishable in IEEE Access easily",
        "easy_win": "Yes — top 10 easy win",
    },
    {
        "task": "Build Urdu Semantic Textual Similarity (STS) Benchmark",
        "category": "Zero-work",
        "effort_level": "Low",
        "effort_hours": "60-80 hrs",
        "compute_level": "Low",
        "gpu_hours": "20-40",
        "data_source": "Translate STSBenchmark (https://github.com/PhilipMay/stsb-multi-mt) via LLM + post-edit; supplement with Urdu news paraphrase pairs from BBC Urdu + Dawn",
        "labeling": "Yes (similarity score 0-5)",
        "annotators": "3 students",
        "expertise": "Students",
        "annotation_weeks": "2-3 weeks",
        "total_weeks": "5-6 weeks",
        "target_venue": "LREC-COLING / SemEval (CCF-B)",
        "roi_score": 9,
        "why_publishable": "No Urdu STS benchmark exists; STSBenchmark translations work for any language",
        "easy_win": "Yes — top 5 easy win",
    },
    {
        "task": "Urdu Keyphrase Extraction (Neural, large-scale)",
        "category": "Tiny-dataset",
        "effort_level": "Low",
        "effort_hours": "60-80 hrs",
        "compute_level": "Low",
        "gpu_hours": "15-30",
        "data_source": "Scrape BBC Urdu (https://www.bbc.com/urdu) + Dawn Urdu news + Jang.com.pk articles; KP-20k-style annotation",
        "labeling": "Yes (keyphrase)",
        "annotators": "2 students",
        "expertise": "Students",
        "annotation_weeks": "3 weeks",
        "total_weeks": "6-7 weeks",
        "target_venue": "IEEE Access / PLOS ONE (Q1 SCI)",
        "roi_score": 8,
        "why_publishable": "Existing Urdu KP work uses tiny corpus; KP-20k format well-established",
        "easy_win": "Yes — top 10 easy win",
    },
    {
        "task": "Urdu News Headline Sarcasm (large)",
        "category": "Tiny-dataset",
        "effort_level": "Low",
        "effort_hours": "50-70 hrs",
        "compute_level": "Low",
        "gpu_hours": "15-30",
        "data_source": "Scrape Jang, Dawn, Express, Nawa-i-Waqt headlines; crowdsource sarcasm labels via Amazon Mechanical Turk or local students",
        "labeling": "Yes (binary)",
        "annotators": "3-5 students",
        "expertise": "Students (Urdu native)",
        "annotation_weeks": "2-3 weeks",
        "total_weeks": "5-6 weeks",
        "target_venue": "IEEE Access (Q1 SCI) / Information Processing & Management (Q1)",
        "roi_score": 8,
        "why_publishable": "Current Urdu sarcasm only 3k tweets — easy to scale to 20k+ headlines",
        "easy_win": "Yes — top 10 easy win",
    },
    {
        "task": "Translate XSum to Urdu (Abstractive Summarization)",
        "category": "Tiny-dataset",
        "effort_level": "Low-Medium",
        "effort_hours": "80-100 hrs",
        "compute_level": "Medium",
        "gpu_hours": "100-200 (mBART fine-tune)",
        "data_source": "BBC XSum (https://github.com/EdinburghNLP/XSum) — translate via LLM; OR scrape BBC Urdu existing summaries directly (BBC Urdu articles have summaries)",
        "labeling": "Yes (minimal post-edit)",
        "annotators": "2 students",
        "expertise": "Students",
        "annotation_weeks": "3-4 weeks",
        "total_weeks": "8-10 weeks",
        "target_venue": "ACL Findings / EMNLP Findings (CCF-A)",
        "roi_score": 8,
        "why_publishable": "UrduSumm only 5k articles; XSum-style benchmark would be first standardized Urdu summarization",
        "easy_win": "Yes — top 10 easy win",
    },
    {
        "task": "Urdu Topic Modeling (Neural, large-scale)",
        "category": "Tiny-dataset",
        "effort_level": "Low",
        "effort_hours": "40-60 hrs",
        "compute_level": "Low",
        "gpu_hours": "10-20",
        "data_source": "Scrape 100k+ BBC Urdu + Dawn news articles using newspaper3k Python lib; no labels needed — unsupervised",
        "labeling": "No",
        "annotators": "0",
        "expertise": "N/A",
        "annotation_weeks": "0",
        "total_weeks": "4-5 weeks",
        "target_venue": "IEEE Access / PLOS ONE (Q1 SCI)",
        "roi_score": 9,
        "why_publishable": "No neural Urdu topic modeling at scale; unsupervised = no annotation cost = easy win",
        "easy_win": "Yes — top 5 easy win",
    },
    {
        "task": "Urdu Readability Assessment (large)",
        "category": "Tiny-dataset",
        "effort_level": "Low",
        "effort_hours": "60-80 hrs",
        "compute_level": "Low",
        "gpu_hours": "15-25",
        "data_source": "Scrape Urdu Wikipedia + BBC Urdu (different grade levels via article categories); label by Flesch-style score adapted for Urdu",
        "labeling": "Yes (readability score)",
        "annotators": "2 students",
        "expertise": "Students + 1 education expert",
        "annotation_weeks": "3 weeks",
        "total_weeks": "6-7 weeks",
        "target_venue": "IEEE Access / PLOS ONE",
        "roi_score": 8,
        "why_publishable": "Existing UrduRead only 3k sentences; needs scaling",
        "easy_win": "Yes — top 10 easy win",
    },
    {
        "task": "Urdu Code-mixed Detection (Roman-Nastaliq switching)",
        "category": "Tiny-dataset",
        "effort_level": "Low",
        "effort_hours": "50-70 hrs",
        "compute_level": "Low",
        "gpu_hours": "10-20",
        "data_source": "Scrape Twitter/X via snscrape for 'Roman Urdu' queries; scrape YouTube Urdu comments via yt-dlp; CMU code-mixed schema",
        "labeling": "Yes (binary: code-mixed or not)",
        "annotators": "2 students",
        "expertise": "Students",
        "annotation_weeks": "2 weeks",
        "total_weeks": "5-6 weeks",
        "target_venue": "LREC-COLING / FIRE (Indian venue)",
        "roi_score": 8,
        "why_publishable": "Existing work focuses on Roman-Eng; Nastaliq-Roman switching unexplored",
        "easy_win": "Yes — top 10 easy win",
    },

    # ===== MEDIUM EFFORT (ROI 6-7) — Decent impact, more work =====
    {
        "task": "Urdu Grammatical Error Correction (GEC)",
        "category": "Zero-work",
        "effort_level": "Medium",
        "effort_hours": "200-300 hrs",
        "compute_level": "Medium",
        "gpu_hours": "200-500 (seq2seq training)",
        "data_source": "Scrape Urdu learner essays from italki.com, Lang-8 (if accessible), Urdu Wikipedia edit history (reverted edits = errors); partner with Allama Iqbal Open University for learner data",
        "labeling": "Yes (GEC annotation is hard)",
        "annotators": "3-4 experts (Urdu language teachers)",
        "expertise": "Urdu language teachers",
        "annotation_weeks": "12-16 weeks",
        "total_weeks": "20-24 weeks",
        "target_venue": "ACL / EMNLP main (CCF-A) / BEA workshop",
        "roi_score": 6,
        "why_publishable": "First Urdu GEC — guaranteed ACL/EMNLP acceptance if quality is good",
        "easy_win": "Medium effort but very high impact",
    },
    {
        "task": "Urdu Cross-Document Event Extraction",
        "category": "Zero-work",
        "effort_level": "Medium-High",
        "effort_hours": "300-400 hrs",
        "compute_level": "Medium",
        "gpu_hours": "100-200",
        "data_source": "Scrape Jang/Dawn news articles on same events (cross-doc); use ACE-2005 schema; cross-link via Wikidata Urdu events",
        "labeling": "Yes (event + arguments)",
        "annotators": "3-4 trained annotators",
        "expertise": "Trained NLP annotators",
        "annotation_weeks": "10-12 weeks",
        "total_weeks": "16-20 weeks",
        "target_venue": "ACL Findings / NAACL (CCF-A)",
        "roi_score": 6,
        "why_publishable": "First Urdu cross-doc EE — fills obvious gap",
        "easy_win": "No — needs proper annotation team",
    },
    {
        "task": "Urdu Long-form QA",
        "category": "Zero-work",
        "effort_level": "Medium",
        "effort_hours": "150-200 hrs",
        "compute_level": "Medium-High",
        "gpu_hours": "300-600 (LLM fine-tune)",
        "data_source": "Urdu Wikipedia (https://ur.wikipedia.org) — 200k+ articles; build ELI5-style long-form QA via GPT-4o generation + human verification",
        "labeling": "Yes (answer verification)",
        "annotators": "2-3 students",
        "expertise": "Students",
        "annotation_weeks": "6-8 weeks",
        "total_weeks": "12-14 weeks",
        "target_venue": "ACL / EMNLP Findings",
        "roi_score": 7,
        "why_publishable": "Only extractive QA exists; long-form is hot in LLM era",
        "easy_win": "No — needs LLM compute",
    },
    {
        "task": "Urdu Multi-hop Reading Comprehension",
        "category": "Tiny-dataset",
        "effort_level": "Medium",
        "effort_hours": "150-200 hrs",
        "compute_level": "Medium",
        "gpu_hours": "100-200",
        "data_source": "Translate HotpotQA (https://hotpotqa.github.io) via LLM; OR build from Urdu Wikipedia multi-page link graph",
        "labeling": "Yes (answer + supporting docs)",
        "annotators": "2-3 students",
        "expertise": "Students",
        "annotation_weeks": "5-6 weeks",
        "total_weeks": "10-12 weeks",
        "target_venue": "ACL Findings / EMNLP Findings",
        "roi_score": 7,
        "why_publishable": "UQuAD only single-hop; multi-hop is natural extension",
        "easy_win": "No",
    },
    {
        "task": "Urdu Multi-modal Sentiment (text + image)",
        "category": "Tiny-dataset",
        "effort_level": "Medium",
        "effort_hours": "150-200 hrs",
        "compute_level": "Medium-High",
        "gpu_hours": "200-400 (multimodal BERT)",
        "data_source": "Scrape Urdu tweets with images via Twitter API; Urdu Instagram posts (legal grey area); YouTube Urdu video thumbnails + comments",
        "labeling": "Yes (3-class sentiment)",
        "annotators": "3 students",
        "expertise": "Students",
        "annotation_weeks": "5-6 weeks",
        "total_weeks": "10-12 weeks",
        "target_venue": "IEEE Access (Q1) / ACM MM workshop",
        "roi_score": 7,
        "why_publishable": "Only 5k pairs exist; multimodal is trendy",
        "easy_win": "No",
    },
    {
        "task": "Urdu Stance Detection (multi-target)",
        "category": "Tiny-dataset",
        "effort_level": "Medium",
        "effort_hours": "100-150 hrs",
        "compute_level": "Low",
        "gpu_hours": "30-60",
        "data_source": "Scrape Twitter debates on Pakistani politics (Imran Khan, PML-N, PPP); SemEval-2016 Task 6 schema; use RumourEval-2019 schema",
        "labeling": "Yes (stance: favor/against/none)",
        "annotators": "3 students",
        "expertise": "Students with political awareness",
        "annotation_weeks": "4-5 weeks",
        "total_weeks": "8-10 weeks",
        "target_venue": "IEEE Access / Information Processing & Management (Q1)",
        "roi_score": 7,
        "why_publishable": "Current Urdu stance work is tiny (2k posts); multi-target is novel angle",
        "easy_win": "No",
    },
    {
        "task": "Urdu Fake News Detection (multimodal)",
        "category": "Tiny-dataset",
        "effort_level": "Medium",
        "effort_hours": "150-200 hrs",
        "compute_level": "Medium",
        "gpu_hours": "100-200",
        "data_source": "Scrape debunked stories from Soch Fact Check (https://sochfactcheck.com), AFP Pakistan Urdu fact-checks; pair with original fake posts on Facebook/Twitter Urdu",
        "labeling": "Yes (fake/real + claim type)",
        "annotators": "2-3 fact-checkers (light training)",
        "expertise": "Junior fact-checkers",
        "annotation_weeks": "5-6 weeks",
        "total_weeks": "10-12 weeks",
        "target_venue": "ACL Findings / PLOS ONE (Q1)",
        "roi_score": 7,
        "why_publishable": "UrduFakeNet only 10k text-only; multimodal + real fact-checker labels is novel",
        "easy_win": "No",
    },
    {
        "task": "Urdu Authorship Attribution (cross-genre)",
        "category": "Tiny-dataset",
        "effort_level": "Medium",
        "effort_hours": "100-150 hrs",
        "compute_level": "Low",
        "gpu_hours": "30-60",
        "data_source": "Project Gutenberg Urdu (https://www.gutenberg.org/browse/languages/ur); Urdu literary archives (Rekhta.org — 80k+ texts); author lists on Jang/Dawn columnists",
        "labeling": "Yes (author ID — already in metadata)",
        "annotators": "0 (label is metadata)",
        "expertise": "N/A",
        "annotation_weeks": "0",
        "total_weeks": "4-6 weeks",
        "target_venue": "PLOS ONE / IEEE Access (Q1)",
        "roi_score": 8,
        "why_publishable": "Metadata labels = no annotation; cross-genre is novel angle",
        "easy_win": "Yes — top 10 easy win (no annotation!)",
    },
    {
        "task": "Urdu Plagiarism Detection (large-scale)",
        "category": "Tiny-dataset",
        "effort_level": "Low-Medium",
        "effort_hours": "80-100 hrs",
        "compute_level": "Low",
        "gpu_hours": "20-40",
        "data_source": "Use Urdu Wikipedia edit history (https://dumps.wikimedia.org/urwiki/) — revert wars = plagiarism; supplement with Urdu research papers from HEC Pakistan repository (https://www.hec.gov.pk)",
        "labeling": "Yes (plagiarism type)",
        "annotators": "1-2 students",
        "expertise": "Students",
        "annotation_weeks": "2-3 weeks",
        "total_weeks": "6-7 weeks",
        "target_venue": "PLOS ONE / Scientometrics (Q1)",
        "roi_score": 8,
        "why_publishable": "Wikipedia edit history = free plagiarism labels; novel for Urdu",
        "easy_win": "Yes — top 10 easy win",
    },
    {
        "task": "Urdu Emotion Cause Extraction (ECE)",
        "category": "Tiny-dataset",
        "effort_level": "Medium",
        "effort_hours": "100-150 hrs",
        "compute_level": "Low",
        "gpu_hours": "30-50",
        "data_source": "Scrape Urdu Twitter emotional posts (use emotion lexicon to filter); RECCON schema annotation",
        "labeling": "Yes (emotion + cause span)",
        "annotators": "3 students",
        "expertise": "Students",
        "annotation_weeks": "4-5 weeks",
        "total_weeks": "8-10 weeks",
        "target_venue": "IEEE Access (Q1) / PLOS ONE",
        "roi_score": 7,
        "why_publishable": "Urdu ECE is at 2k pairs — very small, easy to scale to 10k+",
        "easy_win": "No",
    },
    {
        "task": "Urdu Topic Segmentation (large)",
        "category": "Tiny-dataset",
        "effort_level": "Low-Medium",
        "effort_hours": "80-100 hrs",
        "compute_level": "Low",
        "gpu_hours": "20-40",
        "data_source": "Scrape Wikipedia Urdu articles with section headers — section boundaries ARE topic segmentation labels (free labels!)",
        "labeling": "No (use section headers)",
        "annotators": "0",
        "expertise": "N/A",
        "annotation_weeks": "0",
        "total_weeks": "4-5 weeks",
        "target_venue": "IEEE Access / PLOS ONE",
        "roi_score": 9,
        "why_publishable": "Wikipedia section headers = free labels; current UrduSeg only 2k docs",
        "easy_win": "Yes — top 5 easy win (no annotation!)",
    },
    {
        "task": "Urdu Document Clustering (large-scale)",
        "category": "Tiny-dataset",
        "effort_level": "Low",
        "effort_hours": "50-70 hrs",
        "compute_level": "Low",
        "gpu_hours": "15-30",
        "data_source": "Scrape 50k+ BBC Urdu + Dawn news articles (already categorized by news section = free labels); use 20NewsGroups-style evaluation",
        "labeling": "No (use news categories)",
        "annotators": "0",
        "expertise": "N/A",
        "annotation_weeks": "0",
        "total_weeks": "3-4 weeks",
        "target_venue": "IEEE Access (Q1)",
        "roi_score": 9,
        "why_publishable": "News categories = free labels; easy paper",
        "easy_win": "Yes — top 5 easy win",
    },

    # ===== HIGH EFFORT (ROI 4-5) — Big projects, big publications =====
    {
        "task": "Urdu Legal Document Analysis (Legal-BERT-Urdu)",
        "category": "Zero-work",
        "effort_level": "High",
        "effort_hours": "500-700 hrs",
        "compute_level": "High",
        "gpu_hours": "500-1000",
        "data_source": "Pakistan Supreme Court judgments (https://www.supremecourt.gov.pk); Lahore High Court judgments; India Supreme Court Urdu judgments (https://main.sci.gov.in); CLIC Pakistan (https://clic.org.pk)",
        "labeling": "Yes (legal NER, judgment outcome)",
        "annotators": "3-4 law students",
        "expertise": "Law students",
        "annotation_weeks": "16-20 weeks",
        "total_weeks": "32-40 weeks",
        "target_venue": "Artificial Intelligence and Law (Q1 SCI) / ACL Findings",
        "roi_score": 5,
        "why_publishable": "First Urdu legal NLP — guaranteed AI&Law journal; high social impact",
        "easy_win": "No — requires legal expertise",
    },
    {
        "task": "Urdu Medical QA (MedQA-Urdu)",
        "category": "Zero-work",
        "effort_level": "High",
        "effort_hours": "400-600 hrs",
        "compute_level": "High",
        "gpu_hours": "500-1000 (LLM fine-tune)",
        "data_source": "Translate MedQA (https://github.com/jinjiego/MedQA) via GPT-4o + medical professional post-edit; supplement with Pakistan Medical & Dental Council exam questions (PMDC); Urdu medical articles on Mayoclinic Urdu",
        "labeling": "Yes (medical QA verification)",
        "annotators": "2-3 MBBS doctors",
        "expertise": "Medical doctors",
        "annotation_weeks": "12-16 weeks",
        "total_weeks": "24-30 weeks",
        "target_venue": "JAMIA (Q1 SCI) / JBI (Q1) / ACL Findings",
        "roi_score": 5,
        "why_publishable": "First Urdu medical NLP — huge impact; JAMIA is top medical informatics journal",
        "easy_win": "No — requires MD annotators",
    },
    {
        "task": "Urdu Native LLM (UrduGPT-7B from scratch)",
        "category": "Zero-work",
        "effort_level": "Very High",
        "effort_hours": "1000+ hrs",
        "compute_level": "Very High",
        "gpu_hours": "10,000+ A100 hrs",
        "data_source": "Makhzan + scrape Common Crawl Urdu (https://commoncrawl.org); Urdu Wikipedia full dump; Jang/Dawn archives; Urdu books from Rekhta.org",
        "labeling": "No (self-supervised pre-training)",
        "annotators": "0",
        "expertise": "N/A",
        "annotation_weeks": "0",
        "total_weeks": "20-30 weeks",
        "target_venue": "ACL Main / NeurIPS (CCF-A top tier)",
        "roi_score": 4,
        "why_publishable": "First native Urdu LLM = guaranteed top-venue; but needs big compute budget",
        "easy_win": "No — needs $100k+ compute",
    },
    {
        "task": "Urdu Nastaliq Handwritten OCR (50k+ images)",
        "category": "Tiny-dataset",
        "effort_level": "Very High",
        "effort_hours": "600-800 hrs",
        "compute_level": "Medium-High",
        "gpu_hours": "300-600 (CRNN training)",
        "data_source": "Collect handwritten samples from universities in Pakistan (NUST, FAST, LUMS); partner with Urdu departments; scan historical manuscripts from Punjab Digital Library",
        "labeling": "Yes (line-level transcription)",
        "annotators": "5+ annotators",
        "expertise": "Urdu native readers",
        "annotation_weeks": "20-30 weeks",
        "total_weeks": "30-40 weeks",
        "target_venue": "Pattern Recognition (Q1) / ICDAR (CCF-B)",
        "roi_score": 4,
        "why_publishable": "First public Nastaliq handwritten corpus; ICDAR loves OCR",
        "easy_win": "No — needs physical data collection",
    },
    {
        "task": "Urdu Biomedical NER + Text Mining",
        "category": "Zero-work",
        "effort_level": "High",
        "effort_hours": "400-500 hrs",
        "compute_level": "Medium",
        "gpu_hours": "100-200",
        "data_source": "Translate PubMed abstracts via NLLB-200 + scrape Urdu medical articles from WebMD Urdu, Mayoclinic Urdu, Sehat Kahani (https://sehatkahani.com)",
        "labeling": "Yes (biomedical NER)",
        "annotators": "2-3 medical students",
        "expertise": "Medical students",
        "annotation_weeks": "12-16 weeks",
        "total_weeks": "20-24 weeks",
        "target_venue": "JBI (Q1) / JAMIA / IEEE JBHI",
        "roi_score": 5,
        "why_publishable": "First Urdu biomedical NLP — guaranteed top medical informatics journal",
        "easy_win": "No — needs medical annotators",
    },
    {
        "task": "Urdu Knowledge Graph Construction (Urdu DBpedia)",
        "category": "Zero-work",
        "effort_level": "Very High",
        "effort_hours": "800+ hrs",
        "compute_level": "High",
        "gpu_hours": "500-1000",
        "data_source": "Urdu Wikipedia full dump (https://dumps.wikimedia.org/urwiki/); Wikidata Urdu entities (https://www.wikidata.org); use DBpedia extraction framework",
        "labeling": "Yes (relation triples verification)",
        "annotators": "5+ students",
        "expertise": "Students with ontology training",
        "annotation_weeks": "20+ weeks",
        "total_weeks": "30+ weeks",
        "target_venue": "ISWC (CCF-C top semantic web venue) / KBS (Q1)",
        "roi_score": 4,
        "why_publishable": "First Urdu KG — major undertaking but ISWC loves it",
        "easy_win": "No — massive undertaking",
    },
    {
        "task": "Urdu Few-shot / Zero-shot NER Benchmark",
        "category": "Zero-work",
        "effort_level": "Medium",
        "effort_hours": "150-200 hrs",
        "compute_level": "Medium",
        "gpu_hours": "100-200",
        "data_source": "Use existing CURRE + WikiANN Urdu + new annotation in 5+ domains (news, biomedical, legal, social media, literature)",
        "labeling": "Yes (NER in new domains)",
        "annotators": "3-4 students",
        "expertise": "Students",
        "annotation_weeks": "8-10 weeks",
        "total_weeks": "14-16 weeks",
        "target_venue": "ACL Findings / EMNLP Findings (CCF-A)",
        "roi_score": 6,
        "why_publishable": "Few-shot NER benchmark for Urdu is timely; LLM community cares",
        "easy_win": "No",
    },
    {
        "task": "Urdu Task-Oriented Dialogue (MultiWOZ-style)",
        "category": "Zero-work",
        "effort_level": "High",
        "effort_hours": "400-500 hrs",
        "compute_level": "Medium-High",
        "gpu_hours": "300-500",
        "data_source": "Translate MultiWOZ (https://github.com/budzianowski/multiwoz) via LLM + heavy post-edit; OR build via Wizard-of-Oz experiments with Urdu speakers",
        "labeling": "Yes (dialogue state + intent + slot)",
        "annotators": "4-5 trained annotators",
        "expertise": "Trained NLP annotators",
        "annotation_weeks": "16-20 weeks",
        "total_weeks": "24-30 weeks",
        "target_venue": "ACL Main / EMNLP Main (CCF-A)",
        "roi_score": 5,
        "why_publishable": "First Urdu TOD — guaranteed ACL acceptance",
        "easy_win": "No — heavy annotation",
    },
    {
        "task": "Urdu Fact-checking (claim-evidence)",
        "category": "Zero-work",
        "effort_level": "High",
        "effort_hours": "300-400 hrs",
        "compute_level": "Medium",
        "gpu_hours": "100-200",
        "data_source": "Scrape Soch Fact Check, AFP Pakistan, TruthOrFiction Urdu; pair with original false claims on Facebook Urdu, WhatsApp Urdu forwards (via fact-checking orgs)",
        "labeling": "Yes (claim + evidence + verdict)",
        "annotators": "3-4 trained fact-checkers",
        "expertise": "Trained fact-checkers",
        "annotation_weeks": "12-16 weeks",
        "total_weeks": "20-24 weeks",
        "target_venue": "ACL Findings / PNAS Nexus (Q1)",
        "roi_score": 5,
        "why_publishable": "Hot topic — Urdu misinformation is real problem; high impact",
        "easy_win": "No — requires fact-checking org partnership",
    },
    {
        "task": "Urdu Speech Translation (end-to-end)",
        "category": "Tiny-dataset",
        "effort_level": "Medium-High",
        "effort_hours": "250-350 hrs",
        "compute_level": "High",
        "gpu_hours": "500-1000",
        "data_source": "Extend CoVoST (https://github.com/facebookresearch/covost) with UrduSpeech audio + Urdu-English translations; OR use SeamlessM4T framework on UrduSpeech",
        "labeling": "Yes (audio + translation pairs)",
        "annotators": "2-3 translators",
        "expertise": "Bilingual translators",
        "annotation_weeks": "10-12 weeks",
        "total_weeks": "16-20 weeks",
        "target_venue": "ACL Main / EMNLP Main / Interspeech",
        "roi_score": 5,
        "why_publishable": "End-to-end Urdu ST is missing; SeamlessM4T framework is hot",
        "easy_win": "No",
    },
    {
        "task": "Urdu Sign Language Recognition (large-scale)",
        "category": "Tiny-dataset",
        "effort_level": "Very High",
        "effort_hours": "800+ hrs",
        "compute_level": "High",
        "gpu_hours": "500-1000",
        "data_source": "Partner with Pakistan Association of the Deaf; record videos of native PSL signers; supplement with existing FSL archive",
        "labeling": "Yes (gloss + video)",
        "annotators": "5+ PSL experts + deaf community",
        "expertise": "PSL linguists + deaf community",
        "annotation_weeks": "20+ weeks",
        "total_weeks": "30+ weeks",
        "target_venue": "CVPR / ECCV (CCF-A) / IEEE TPAMI",
        "roi_score": 4,
        "why_publishable": "First large-scale Urdu sign language dataset — major social impact",
        "easy_win": "No — requires deaf community partnership",
    },
    {
        "task": "Urdu Cross-lingual Document Alignment at Scale",
        "category": "Zero-work",
        "effort_level": "Medium",
        "effort_hours": "150-200 hrs",
        "compute_level": "Medium",
        "gpu_hours": "100-200",
        "data_source": "Wikipedia inter-language links (Urdu↔English); BBC Urdu (https://www.bbc.com/urdu) + BBC English parallel articles; OPUS (https://opus.nlpl.eu) Urdu-English",
        "labeling": "No (auto-aligned via Wikipedia interlinks + URL matching)",
        "annotators": "0",
        "expertise": "N/A",
        "annotation_weeks": "0",
        "total_weeks": "6-8 weeks",
        "target_venue": "LREC-COLING / TACL (CCF-A)",
        "roi_score": 8,
        "why_publishable": "Wikipedia interlinks = free alignment; huge IR/MT value",
        "easy_win": "Yes — top 10 easy win (no annotation!)",
    },
    {
        "task": "Urdu Entity Linking (Wikipedia-based)",
        "category": "Zero-work",
        "effort_level": "Medium",
        "effort_hours": "150-200 hrs",
        "compute_level": "Medium",
        "gpu_hours": "100-200",
        "data_source": "Urdu Wikipedia (200k+ articles); use AIDA-CoNLL schema; auto-generate candidates via Wikipedia links, then human-verify",
        "labeling": "Yes (entity verification)",
        "annotators": "2-3 students",
        "expertise": "Students",
        "annotation_weeks": "6-8 weeks",
        "total_weeks": "10-12 weeks",
        "target_venue": "ACL Findings / EMNLP Findings (CCF-A)",
        "roi_score": 7,
        "why_publishable": "First Urdu EL — high practical value for IR",
        "easy_win": "No",
    },
    {
        "task": "Urdu Verbal Irony Detection (distinct from sarcasm)",
        "category": "Zero-work",
        "effort_level": "Low-Medium",
        "effort_hours": "80-100 hrs",
        "compute_level": "Low",
        "gpu_hours": "20-40",
        "data_source": "Scrape Urdu Twitter + Reddit /r/pakistan; use Magpie (https://github.com/irina-shengling/magpie) schema adapted for Urdu",
        "labeling": "Yes (irony type + binary)",
        "annotators": "3 students",
        "expertise": "Students (literature background preferred)",
        "annotation_weeks": "3-4 weeks",
        "total_weeks": "7-8 weeks",
        "target_venue": "IEEE Access / PLOS ONE",
        "roi_score": 7,
        "why_publishable": "Distinct from sarcasm = novel angle; Urdu has rich irony tradition",
        "easy_win": "No",
    },
    {
        "task": "Urdu Personality Detection from Text",
        "category": "Zero-work",
        "effort_level": "Low",
        "effort_hours": "60-80 hrs",
        "compute_level": "Low",
        "gpu_hours": "20-30",
        "data_source": "Translate Essays dataset (https://github.com/SvenBuechel/essays) via LLM; OR scrape Urdu blogs + author MBTI tags from personality forums",
        "labeling": "Yes (MBTI / Big Five)",
        "annotators": "2 students",
        "expertise": "Psychology students preferred",
        "annotation_weeks": "2-3 weeks",
        "total_weeks": "5-6 weeks",
        "target_venue": "IEEE Access / PLOS ONE",
        "roi_score": 8,
        "why_publishable": "First Urdu personality detection — easy novelty",
        "easy_win": "Yes — top 10 easy win",
    },
    {
        "task": "Urdu Disfluency Detection (spoken Urdu)",
        "category": "Zero-work",
        "effort_level": "Medium",
        "effort_hours": "150-200 hrs",
        "compute_level": "Low",
        "gpu_hours": "30-60",
        "data_source": "UrduSpeech (156 hrs) — transcribe with Whisper-large, then annotate disfluencies; OR run new interviews with Pakistani speakers",
        "labeling": "Yes (disfluency span)",
        "annotators": "3 students",
        "expertise": "Students with phonetics training",
        "annotation_weeks": "8-10 weeks",
        "total_weeks": "14-16 weeks",
        "target_venue": "Interspeech / ACL Findings",
        "roi_score": 6,
        "why_publishable": "First Urdu disfluency work — important for spoken Urdu understanding",
        "easy_win": "No",
    },
    {
        "task": "Urdu Math Word Problems",
        "category": "Zero-work",
        "effort_level": "Low",
        "effort_hours": "60-80 hrs",
        "compute_level": "Low",
        "gpu_hours": "20-40",
        "data_source": "Translate ASDiv (https://github.com/google-research-datasets/asdiv) + AQuA via LLM; numbers stay same; minimal post-edit",
        "labeling": "Yes (answer verification)",
        "annotators": "1-2 students",
        "expertise": "Students (math background)",
        "annotation_weeks": "2 weeks",
        "total_weeks": "5-6 weeks",
        "target_venue": "ACL Findings / EMNLP Findings",
        "roi_score": 9,
        "why_publishable": "First Urdu MWP — easy translation, big educational impact",
        "easy_win": "Yes — top 5 easy win",
    },
    {
        "task": "Urdu Trustworthiness Evaluation Benchmark for LLMs",
        "category": "Zero-work",
        "effort_level": "Medium",
        "effort_hours": "200-300 hrs",
        "compute_level": "Medium",
        "gpu_hours": "200-400",
        "data_source": "Translate TrustLLM benchmark (https://trustllm.github.io) via LLM + cultural adaptation; OR build new with Pakistani cultural context",
        "labeling": "Yes (toxicity / fairness / robustness labels)",
        "annotators": "3-4 students",
        "expertise": "Students",
        "annotation_weeks": "6-8 weeks",
        "total_weeks": "12-14 weeks",
        "target_venue": "ACL Findings / NeurIPS Datasets Track",
        "roi_score": 7,
        "why_publishable": "Trustworthy AI is hot topic; first Urdu trust benchmark",
        "easy_win": "No",
    },
    {
        "task": "Urdu Geolocation Prediction from Text",
        "category": "Zero-work",
        "effort_level": "Low-Medium",
        "effort_hours": "80-100 hrs",
        "compute_level": "Low",
        "gpu_hours": "20-40",
        "data_source": "Scrape Twitter Urdu tweets with geolocation enabled (use Twitter Academic API or snscrape); OR use Urdu news with city tags (Jang city-specific pages)",
        "labeling": "Yes (geo coordinate — auto from metadata)",
        "annotators": "0 (metadata = label)",
        "expertise": "N/A",
        "annotation_weeks": "0",
        "total_weeks": "4-5 weeks",
        "target_venue": "IEEE Access / TIST",
        "roi_score": 9,
        "why_publishable": "Geo metadata = free labels; first Urdu geolocation work",
        "easy_win": "Yes — top 5 easy win (no annotation!)",
    },
    {
        "task": "Urdu Document-to-Document Similarity (large-scale)",
        "category": "Zero-work",
        "effort_level": "Low",
        "effort_hours": "50-70 hrs",
        "compute_level": "Low",
        "gpu_hours": "15-30",
        "data_source": "Urdu Wikipedia article pairs via interlanguage links (same article in Urdu + English); OR BBC Urdu same-day articles on same topic",
        "labeling": "No (similarity auto-computed)",
        "annotators": "0",
        "expertise": "N/A",
        "annotation_weeks": "0",
        "total_weeks": "3-4 weeks",
        "target_venue": "IEEE Access (Q1)",
        "roi_score": 9,
        "why_publishable": "Free labels via Wikipedia; easy paper",
        "easy_win": "Yes — top 5 easy win (no annotation!)",
    },
]

print(f"Total feasibility entries: {len(FEASIBILITY)}")

# Sort by ROI score (descending) — best opportunities first
FEASIBILITY.sort(key=lambda x: (-x["roi_score"], x["effort_hours"]))

# Load workbook
WB_PATH = "/home/z/my-project/download/Urdu_NLP_Research_Survey.xlsx"
wb = load_workbook(WB_PATH)

# Remove existing Sheet 6 if it exists
if "6. Feasibility & ROI" in wb.sheetnames:
    del wb["6. Feasibility & ROI"]

ws6 = wb.create_sheet("6. Feasibility & ROI")
ws6.sheet_view.showGridLines = False

# Title
ws6["A1"] = "Feasibility & ROI Analysis — Which Gaps Are Easy Wins for Reputable Journals?"
ws6.merge_cells("A1:N1")
apply_style(ws6["A1"], {
    "font": Font(name=FONT_NAME, size=16, bold=True, color=PRIMARY),
    "alignment": Alignment(horizontal="left", vertical="center"),
})
ws6.row_dimensions[1].height = 28

# Methodology box
ws6["A3"] = ("Methodology: ROI score = (Impact × Publication Potential) ÷ (Effort × Compute × Labeling cost). "
             "Higher ROI = bigger bang for buck. Sorted by ROI descending — top entries are your easiest paths to Q1/CCF-A publications. "
             "Look for entries tagged 'top 5 easy win' — these are low effort, high impact, minimal annotation.")
ws6.merge_cells("A3:N3")
apply_style(ws6["A3"], {
    "font": Font(name=FONT_NAME, size=10, italic=True, color="555555"),
    "alignment": Alignment(horizontal="left", vertical="center", wrap_text=True),
})
ws6.row_dimensions[3].height = 50

# Quick ROI legend
ws6["A5"] = "ROI Score Interpretation:"
ws6.merge_cells("A5:N5")
apply_style(ws6["A5"], {
    "font": Font(name=FONT_NAME, size=11, bold=True, color=PRIMARY),
    "alignment": Alignment(horizontal="left", vertical="center"),
})

legend = [
    ("9-10", "EASY WIN — low effort, high impact, minimal/no annotation. Submit to Q1/CCF-A in 4-10 weeks.", GAP_NONE),
    ("7-8", "GOOD OPPORTUNITY — moderate effort, decent impact. Submit to Q1/CCF-A in 8-16 weeks.", "E8F5E9"),
    ("5-6", "BIG PROJECT — high effort but big publication. Submit to top venue in 16-30 weeks.", GAP_HIGH),
    ("1-4", "MAJOR UNDERTAKING — needs team + compute budget + domain experts. 6-12 month commitment.", GAP_CRITICAL),
]

row = 6
for score_range, desc, bg_color in legend:
    ws6.cell(row=row, column=1, value=score_range).fill = PatternFill("solid", fgColor=bg_color)
    ws6.cell(row=row, column=1).font = Font(name=FONT_NAME, size=11, bold=True)
    ws6.cell(row=row, column=1).alignment = Alignment(horizontal="center", vertical="center")
    ws6.cell(row=row, column=1).border = thin_border()
    ws6.cell(row=row, column=2, value=desc)
    ws6.merge_cells(start_row=row, start_column=2, end_row=row, end_column=14)
    apply_style(ws6.cell(row=row, column=2), body_style(bg=bg_color, size=10))
    row += 1

# Header row
header_row = 11
headers6 = [
    "#", "ROI Score", "Easy Win?", "Task / Gap to Fill", "Category",
    "Effort Level", "Effort (hours)", "Compute", "GPU Hours",
    "Data Source (where to scrape)", "Labeling Required?",
    "# Annotators / Expertise", "Annotation Time",
    "Total Calendar Time", "Target Venue (Q1 / CCF-A)",
    "Why Publishable"
]

# Adjust merge: we have 16 columns now
ws6.merge_cells(start_row=1, start_column=1, end_row=1, end_column=16)
ws6.merge_cells(start_row=3, start_column=1, end_row=3, end_column=16)
ws6.merge_cells(start_row=5, start_column=1, end_row=5, end_column=16)

# Update legend rows to merge 2-16
for r in range(6, 10):
    try:
        ws6.unmerge_cells(start_row=r, start_column=2, end_row=r, end_column=14)
    except:
        pass
    ws6.merge_cells(start_row=r, start_column=2, end_row=r, end_column=16)

for col, h in enumerate(headers6, 1):
    c = ws6.cell(row=header_row, column=col, value=h)
    apply_style(c, header_style())
ws6.row_dimensions[header_row].height = 50

# Write entries
for i, f in enumerate(FEASIBILITY, 1):
    r = header_row + i
    bg = ALT_ROW if i % 2 == 0 else None
    
    # Color code by ROI
    roi = f["roi_score"]
    if roi >= 9:
        roi_bg = GAP_NONE
        roi_color = SUCCESS
    elif roi >= 7:
        roi_bg = "E8F5E9"
        roi_color = SUCCESS
    elif roi >= 5:
        roi_bg = GAP_HIGH
        roi_color = WARNING
    else:
        roi_bg = GAP_CRITICAL
        roi_color = DANGER
    
    easy_win = f["easy_win"]
    ew_color = SUCCESS if "Yes" in easy_win else (WARNING if "Medium" in easy_win else "9E9E9E")
    
    eff_color = {"Low": SUCCESS, "Low-Medium": "FB8C00", "Medium": WARNING, "Medium-High": DANGER, "High": DANGER, "Very High": DANGER}.get(f["effort_level"], "000000")
    comp_color = {"Low": SUCCESS, "Low-Medium": "FB8C00", "Medium": WARNING, "Medium-High": DANGER, "High": DANGER, "Very High": DANGER}.get(f["compute_level"], "000000")
    lab_color = {"No": SUCCESS, "Yes (minimal — answer validation)": SUCCESS, "Yes (minimal post-edit)": SUCCESS, "Yes (3-class sentiment)": WARNING}.get(f["labeling"], WARNING)
    # Default for any "Yes"
    if f["labeling"].startswith("Yes"):
        if "minimal" in f["labeling"] or "auto" in f["labeling"].lower():
            lab_color = SUCCESS
        elif "binary" in f["labeling"] or "3-class" in f["labeling"] or "metadata" in f["labeling"].lower():
            lab_color = WARNING
        else:
            lab_color = DANGER
    else:
        lab_color = SUCCESS
    
    values = [
        i,
        roi,
        easy_win,
        f["task"],
        f["category"],
        f["effort_level"],
        f["effort_hours"],
        f["compute_level"],
        f["gpu_hours"],
        f["data_source"],
        f["labeling"],
        f["annotators"] + " — " + f["expertise"],
        f["annotation_weeks"],
        f["total_weeks"],
        f["target_venue"],
        f["why_publishable"],
    ]
    
    for col, v in enumerate(values, 1):
        cell = ws6.cell(row=r, column=col, value=v)
        if col == 1:  # #
            apply_style(cell, body_style(bold=True, align="center", bg=bg))
        elif col == 2:  # ROI
            apply_style(cell, body_style(bold=True, align="center", color=roi_color, bg=roi_bg, size=12))
        elif col == 3:  # Easy win
            apply_style(cell, body_style(align="center", bold=True, color=ew_color, bg=bg, size=9))
        elif col == 4:  # Task
            apply_style(cell, body_style(bold=True, color=PRIMARY, bg=bg))
        elif col == 5:  # Category
            apply_style(cell, body_style(align="center", bg=bg, size=9))
        elif col == 6:  # Effort level
            apply_style(cell, body_style(align="center", bold=True, color=eff_color, bg=bg, size=9))
        elif col == 7:  # Effort hours
            apply_style(cell, body_style(align="center", bg=bg, size=9))
        elif col == 8:  # Compute
            apply_style(cell, body_style(align="center", bold=True, color=comp_color, bg=bg, size=9))
        elif col == 9:  # GPU hours
            apply_style(cell, body_style(align="center", bg=bg, size=9))
        elif col == 10:  # Data source
            apply_style(cell, body_style(bg=bg, size=8, color="0563C1"))
        elif col == 11:  # Labeling
            apply_style(cell, body_style(align="center", bold=True, color=lab_color, bg=bg, size=9))
        elif col == 12:  # Annotators
            apply_style(cell, body_style(bg=bg, size=9))
        elif col == 13:  # Annotation time
            apply_style(cell, body_style(align="center", bg=bg, size=9))
        elif col == 14:  # Total time
            apply_style(cell, body_style(align="center", bold=True, bg=bg, size=9))
        elif col == 15:  # Target venue
            apply_style(cell, body_style(bg=bg, size=9, bold=True, color=PRIMARY))
        else:  # Why publishable
            apply_style(cell, body_style(bg=bg, size=9, color="333333"))

# Set column widths
widths6 = {
    1: 4,   # #
    2: 7,   # ROI
    3: 14,  # Easy win
    4: 32,  # Task
    5: 11,  # Category
    6: 11,  # Effort level
    7: 13,  # Effort hours
    8: 11,  # Compute
    9: 16,  # GPU hours
    10: 50, # Data source
    11: 22, # Labeling
    12: 28, # Annotators
    13: 12, # Annotation time
    14: 13, # Total time
    15: 30, # Target venue
    16: 40, # Why publishable
}
for c, w in widths6.items():
    ws6.column_dimensions[get_column_letter(c)].width = w

ws6.freeze_panes = "A12"
ws6.auto_filter.ref = f"A11:P{11 + len(FEASIBILITY)}"

# Add a "Top 5 Easy Wins" highlight box at the bottom
top_row = 11 + len(FEASIBILITY) + 3
ws6.cell(row=top_row, column=1, value="TOP 5 EASY WINS — Do These First (highest ROI, lowest effort)")
ws6.merge_cells(start_row=top_row, start_column=1, end_row=top_row, end_column=16)
apply_style(ws6.cell(row=top_row, column=1), {
    "font": Font(name=FONT_NAME, size=14, bold=True, color=SUCCESS),
    "fill": PatternFill("solid", fgColor=GAP_NONE),
    "alignment": Alignment(horizontal="left", vertical="center"),
})
ws6.row_dimensions[top_row].height = 26

top5 = [f for f in FEASIBILITY if "top 5" in f["easy_win"]][:5]
for i, f in enumerate(top5, 1):
    r = top_row + i
    bg = ALT_ROW if i % 2 == 0 else None
    ws6.cell(row=r, column=1, value=i).alignment = Alignment(horizontal="center")
    ws6.cell(row=r, column=1).font = Font(name=FONT_NAME, size=11, bold=True, color=SUCCESS)
    ws6.cell(row=r, column=2, value=f"ROI {f['roi_score']}/10").alignment = Alignment(horizontal="center")
    ws6.cell(row=r, column=2).font = Font(name=FONT_NAME, size=11, bold=True, color=SUCCESS)
    ws6.cell(row=r, column=3, value=f["task"]).font = Font(name=FONT_NAME, size=11, bold=True, color=PRIMARY)
    ws6.merge_cells(start_row=r, start_column=3, end_row=r, end_column=8)
    ws6.cell(row=r, column=9, value=f"Effort: {f['effort_level']} ({f['effort_hours']})").font = Font(name=FONT_NAME, size=10)
    ws6.merge_cells(start_row=r, start_column=9, end_row=r, end_column=11)
    ws6.cell(row=r, column=12, value=f"Compute: {f['compute_level']} ({f['gpu_hours']})").font = Font(name=FONT_NAME, size=10)
    ws6.merge_cells(start_row=r, start_column=12, end_row=r, end_column=14)
    ws6.cell(row=r, column=15, value=f"Target: {f['target_venue']}").font = Font(name=FONT_NAME, size=10, italic=True, color=SUCCESS)
    ws6.merge_cells(start_row=r, start_column=15, end_row=r, end_column=16)
    for c in range(1, 17):
        ws6.cell(row=r, column=c).border = thin_border()
        if bg:
            ws6.cell(row=r, column=c).fill = PatternFill("solid", fgColor=bg)
    ws6.row_dimensions[r].height = 22

print(f"Sheet 6 (Feasibility & ROI) done. {len(FEASIBILITY)} entries listed.")

# Save
wb.save(WB_PATH)
print(f"\n✅ Excel file saved: {WB_PATH}")
print(f"Total sheets: {len(wb.sheetnames)}")
for s in wb.sheetnames:
    print(f"  - {s}")
