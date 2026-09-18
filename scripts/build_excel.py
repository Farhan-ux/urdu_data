"""
Build the comprehensive Urdu NLP Excel workbook.
5 sheets: Summary Dashboard, All Papers, Task Coverage, Dataset Catalog, Gap Analysis
"""
import sys, os, json, re
from collections import Counter, defaultdict
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Border, Side, Alignment
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, PieChart, Reference
from openpyxl.formatting.rule import CellIsRule, ColorScaleRule

sys.path.insert(0, "/home/z/my-project/scripts")
from papers_data import PAPERS

# Load URL status
with open("/home/z/my-project/research/url_status.json") as f:
    URL_STATUS = json.load(f)

# ============================================================
# DESIGN TOKENS
# ============================================================
PRIMARY = "1F4E79"      # deep blue
ACCENT = "C00000"        # deep red
SUCCESS = "2E7D32"       # green
WARNING = "ED6C02"       # orange
DANGER = "C62828"        # red
LIGHT_BG = "F4F6F9"      # very light grey-blue
ALT_ROW = "FAFBFC"       # alternating row
HEADER_BG = "1F4E79"     # primary
HEADER_FG = "FFFFFF"
KPI_BG = "E8F1FA"        # light blue for KPI cards
GAP_CRITICAL = "FCE4E4"  # red-ish for critical gaps
GAP_HIGH = "FFF4E4"      # orange-ish for high gaps
GAP_NONE = "E8F5E9"      # green for no gap

FONT_NAME = "Calibri"

# ============================================================
# STYLE HELPERS
# ============================================================
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
# WORKBOOK INIT
# ============================================================
wb = Workbook()
wb.properties.creator = "Z.ai"
wb.properties.title = "Urdu NLP Research Papers — Comprehensive Survey"
wb.properties.subject = "Urdu NLP papers, datasets, tasks, gaps"

# Remove default sheet
wb.remove(wb.active)

# ============================================================
# SHEET 1: SUMMARY DASHBOARD
# ============================================================
ws = wb.create_sheet("1. Summary Dashboard")
ws.sheet_view.showGridLines = False

# Title
ws["A1"] = "Urdu NLP Research — Comprehensive Survey & Gap Analysis"
ws.merge_cells("A1:H1")
apply_style(ws["A1"], {
    "font": Font(name=FONT_NAME, size=20, bold=True, color=PRIMARY),
    "alignment": Alignment(horizontal="left", vertical="center"),
})
ws.row_dimensions[1].height = 32

ws["A2"] = "Compiled from ACL Anthology, arXiv, IEEE, ACM, Springer, Elsevier, MDPI, FIRE, LREC, ICON, plus direct dataset repositories (GitHub, HuggingFace, Zenodo)"
ws.merge_cells("A2:H2")
apply_style(ws["A2"], {
    "font": Font(name=FONT_NAME, size=10, italic=True, color="666666"),
    "alignment": Alignment(horizontal="left", vertical="center"),
})
ws.row_dimensions[2].height = 18

# KPI cards
ws["A4"] = "Headline Statistics"
ws.merge_cells("A4:H4")
apply_style(ws["A4"], {
    "font": Font(name=FONT_NAME, size=14, bold=True, color=PRIMARY),
    "alignment": Alignment(horizontal="left", vertical="center"),
    "border": Border(bottom=Side(style="medium", color=PRIMARY)),
})

kpis = [
    ("Total Papers Catalogued", len(PAPERS), PRIMARY),
    ("Unique NLP Tasks Covered", len(set(p["task"] for p in PAPERS)), ACCENT),
    ("Unique Datasets Identified", len(set(p["dataset"] for p in PAPERS if p["dataset"] and p["dataset"] != "N/A")), "7B1FA2"),
    ("Datasets Public (Lenient)", sum(1 for p in PAPERS if p["public"] in ("Yes", "Partial")), SUCCESS),
    ("Datasets Behind Request/No", sum(1 for p in PAPERS if p["public"] in ("No", "Request")), DANGER),
    ("URLs Verified Broken", sum(1 for v in URL_STATUS.values() if v.startswith("Broken")), WARNING),
]

row = 6
col = 1
for label, value, color in kpis:
    # KPI value cell
    cell_val = ws.cell(row=row, column=col, value=value)
    cell_val.fill = PatternFill("solid", fgColor=KPI_BG)
    cell_val.font = Font(name=FONT_NAME, size=24, bold=True, color=color)
    cell_val.alignment = Alignment(horizontal="center", vertical="center")
    cell_val.border = thin_border()
    ws.row_dimensions[row].height = 38
    ws.row_dimensions[row+1].height = 22
    # Label cell
    cell_lab = ws.cell(row=row+1, column=col, value=label)
    cell_lab.fill = PatternFill("solid", fgColor=KPI_BG)
    cell_lab.font = Font(name=FONT_NAME, size=10, bold=True, color="333333")
    cell_lab.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell_lab.border = thin_border()
    col += 1

# Section: Papers by Year
row = 10
ws.cell(row=row, column=1, value="Papers by Year").font = Font(name=FONT_NAME, size=14, bold=True, color=PRIMARY)
ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=4)
row += 1

years = Counter(p["year"] for p in PAPERS)
sorted_years = sorted(years.items())
ws.cell(row=row, column=1, value="Year").fill = PatternFill("solid", fgColor=HEADER_BG)
ws.cell(row=row, column=1).font = Font(name=FONT_NAME, size=10, bold=True, color=HEADER_FG)
ws.cell(row=row, column=1).alignment = Alignment(horizontal="center")
ws.cell(row=row, column=2, value="Papers").fill = PatternFill("solid", fgColor=HEADER_BG)
ws.cell(row=row, column=2).font = Font(name=FONT_NAME, size=10, bold=True, color=HEADER_FG)
ws.cell(row=row, column=2).alignment = Alignment(horizontal="center")
for c in (1, 2):
    ws.cell(row=row, column=c).border = thin_border()

for i, (y, c) in enumerate(sorted_years):
    r = row + 1 + i
    ws.cell(row=r, column=1, value=y).border = thin_border()
    ws.cell(row=r, column=1).alignment = Alignment(horizontal="center")
    ws.cell(row=r, column=2, value=c).border = thin_border()
    ws.cell(row=r, column=2).alignment = Alignment(horizontal="center")

# Bar chart: papers by year
chart = BarChart()
chart.type = "col"
chart.style = 11
chart.title = "Urdu NLP Papers per Year"
chart.y_axis.title = "Count"
chart.x_axis.title = "Year"
chart.height = 8
chart.width = 18
data = Reference(ws, min_col=2, min_row=row, max_row=row + len(sorted_years), max_col=2)
cats = Reference(ws, min_col=1, min_row=row + 1, max_row=row + len(sorted_years))
chart.add_data(data, titles_from_data=True)
chart.set_categories(cats)
ws.add_chart(chart, f"D{row}")

# Section: Top tasks
row = row + len(sorted_years) + 12
ws.cell(row=row, column=1, value="Top 15 NLP Tasks by Paper Count").font = Font(name=FONT_NAME, size=14, bold=True, color=PRIMARY)
ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=4)
row += 1

tasks_count = Counter(p["task"] for p in PAPERS)
top_tasks = tasks_count.most_common(15)

ws.cell(row=row, column=1, value="Task").fill = PatternFill("solid", fgColor=HEADER_BG)
ws.cell(row=row, column=1).font = Font(name=FONT_NAME, size=10, bold=True, color=HEADER_FG)
ws.cell(row=row, column=1).alignment = Alignment(horizontal="center")
ws.cell(row=row, column=2, value="Papers").fill = PatternFill("solid", fgColor=HEADER_BG)
ws.cell(row=row, column=2).font = Font(name=FONT_NAME, size=10, bold=True, color=HEADER_FG)
ws.cell(row=row, column=2).alignment = Alignment(horizontal="center")
for c in (1, 2):
    ws.cell(row=row, column=c).border = thin_border()

for i, (t, c) in enumerate(top_tasks):
    r = row + 1 + i
    ws.cell(row=r, column=1, value=t).border = thin_border()
    ws.cell(row=r, column=2, value=c).border = thin_border()
    ws.cell(row=r, column=2).alignment = Alignment(horizontal="center")

# Pie chart for tasks
pie = PieChart()
pie.title = "Top 15 Urdu NLP Tasks"
pie.height = 10
pie.width = 14
data = Reference(ws, min_col=2, min_row=row, max_row=row + 15, max_col=2)
cats = Reference(ws, min_col=1, min_row=row + 1, max_row=row + 15)
pie.add_data(data, titles_from_data=True)
pie.set_categories(cats)
ws.add_chart(pie, f"D{row}")

# Public availability summary
row = row + 17
ws.cell(row=row, column=1, value="Dataset Public Availability (Lenient Rule)").font = Font(name=FONT_NAME, size=14, bold=True, color=PRIMARY)
ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=4)
row += 1
ws.cell(row=row, column=1, value="Status").fill = PatternFill("solid", fgColor=HEADER_BG)
ws.cell(row=row, column=1).font = Font(name=FONT_NAME, size=10, bold=True, color=HEADER_FG)
ws.cell(row=row, column=1).alignment = Alignment(horizontal="center")
ws.cell(row=row, column=2, value="Count").fill = PatternFill("solid", fgColor=HEADER_BG)
ws.cell(row=row, column=2).font = Font(name=FONT_NAME, size=10, bold=True, color=HEADER_FG)
ws.cell(row=row, column=2).alignment = Alignment(horizontal="center")
ws.cell(row=row, column=3, value="Meaning").fill = PatternFill("solid", fgColor=HEADER_BG)
ws.cell(row=row, column=3).font = Font(name=FONT_NAME, size=10, bold=True, color=HEADER_FG)
ws.cell(row=row, column=3).alignment = Alignment(horizontal="center")
for c in (1, 2, 3):
    ws.cell(row=row, column=c).border = thin_border()

pub_counter = Counter(p["public"] for p in PAPERS)
pub_meaning = {
    "Yes": "Publicly downloadable (GitHub/HF/Zenodo/aclanthology)",
    "No": "No public access — used privately by paper authors",
    "Request": "Mentioned as available 'on request' from authors / institution",
    "Partial": "Part of the dataset is public; rest is gated",
    "N/A": "Survey paper or pure resource-paper with no dataset",
}
for i, (k, v) in enumerate(sorted(pub_counter.items(), key=lambda x: -x[1])):
    r = row + 1 + i
    ws.cell(row=r, column=1, value=k).border = thin_border()
    ws.cell(row=r, column=2, value=v).border = thin_border()
    ws.cell(row=r, column=2).alignment = Alignment(horizontal="center")
    ws.cell(row=r, column=3, value=pub_meaning.get(k, "")).border = thin_border()

# Set column widths for dashboard
widths = {1: 22, 2: 14, 3: 50, 4: 14, 5: 14, 6: 14, 7: 14, 8: 14}
for c, w in widths.items():
    ws.column_dimensions[get_column_letter(c)].width = w

print("Sheet 1 (Summary Dashboard) done.")

# ============================================================
# SHEET 2: ALL PAPERS
# ============================================================
ws2 = wb.create_sheet("2. All Papers")
ws2.sheet_view.showGridLines = False

# Title
ws2["A1"] = "All Urdu NLP Papers Catalogued (250 entries)"
ws2.merge_cells("A1:N1")
apply_style(ws2["A1"], {
    "font": Font(name=FONT_NAME, size=16, bold=True, color=PRIMARY),
    "alignment": Alignment(horizontal="left", vertical="center"),
})
ws2.row_dimensions[1].height = 28

# Header row
headers = ["#", "Title", "Authors", "Year", "Venue", "NLP Task", "Sub-task", "Dataset Used",
           "Model / Method", "Reported Score", "Dataset URL", "Public?", "URL Status", "Notes"]

for col, h in enumerate(headers, 1):
    c = ws2.cell(row=3, column=col, value=h)
    apply_style(c, header_style())
ws2.row_dimensions[3].height = 36

# Data rows
for i, p in enumerate(PAPERS, 1):
    r = 3 + i
    row_bg = ALT_ROW if i % 2 == 0 else None
    
    # URL status from verification
    dataset_url = p.get("dataset_url", "")
    url_status = ""
    if dataset_url and dataset_url.startswith("http"):
        s = URL_STATUS.get(dataset_url, "")
        if s.startswith("OK"):
            url_status = "OK"
        elif s.startswith("Broken"):
            url_status = "Broken"
        elif s == "Timeout":
            url_status = "Timeout"
        elif s == "Skipped":
            url_status = "Skipped"
        else:
            url_status = "Unknown"
    
    public = p["public"]
    pub_color = {
        "Yes": SUCCESS,
        "No": DANGER,
        "Request": WARNING,
        "Partial": "FB8C00",
        "N/A": "9E9E9E",
    }.get(public, "000000")
    
    values = [
        i,
        p["title"],
        p["authors"],
        p["year"],
        p["venue"],
        p["task"],
        p["sub_task"],
        p["dataset"],
        p["model"],
        p["score"],
        dataset_url,
        public,
        url_status,
        p["notes"],
    ]
    
    for col, v in enumerate(values, 1):
        cell = ws2.cell(row=r, column=col, value=v)
        if col == 1:  # #
            apply_style(cell, body_style(bold=True, align="center", bg=row_bg))
        elif col == 4:  # Year
            apply_style(cell, body_style(align="center", bg=row_bg))
        elif col == 6:  # Task
            apply_style(cell, body_style(bold=True, color=PRIMARY, bg=row_bg))
        elif col == 12:  # Public?
            apply_style(cell, body_style(bold=True, color=pub_color, align="center", bg=row_bg))
        elif col == 13:  # URL status
            status_color = SUCCESS if url_status == "OK" else (DANGER if url_status == "Broken" else "9E9E9E")
            apply_style(cell, body_style(align="center", color=status_color, bg=row_bg))
        elif col in (11,):  # URL
            apply_style(cell, body_style(size=9, color="0563C1", bg=row_bg))
            cell.hyperlink = v if v else None
        else:
            apply_style(cell, body_style(bg=row_bg))

# Column widths
col_widths = {
    1: 5,   # #
    2: 60,  # Title
    3: 28,  # Authors
    4: 7,   # Year
    5: 22,  # Venue
    6: 18,  # Task
    7: 18,  # Sub-task
    8: 28,  # Dataset
    9: 22,  # Model
    10: 14, # Score
    11: 35, # URL
    12: 10, # Public
    13: 10, # URL status
    14: 35, # Notes
}
for c, w in col_widths.items():
    ws2.column_dimensions[get_column_letter(c)].width = w

# Freeze panes
ws2.freeze_panes = "A4"

# Auto-filter
ws2.auto_filter.ref = f"A3:N{3 + len(PAPERS)}"

print("Sheet 2 (All Papers) done.")

# ============================================================
# SHEET 3: TASK COVERAGE
# ============================================================
ws3 = wb.create_sheet("3. Task Coverage")
ws3.sheet_view.showGridLines = False

ws3["A1"] = "NLP Task Coverage Analysis — Urdu vs General NLP Maturity"
ws3.merge_cells("A1:G1")
apply_style(ws3["A1"], {
    "font": Font(name=FONT_NAME, size=16, bold=True, color=PRIMARY),
})
ws3.row_dimensions[1].height = 28

# Explanation
ws3["A3"] = "How to read: Maturity levels — 'None' = no Urdu work exists; 'Small' = <5 papers; 'Emerging' = 5-15 papers; 'Mature' = 15+ papers. Gap Level — 'Critical' = zero/small work on small dataset; 'High' = limited work, dataset <10k; 'Medium' = some work, decent dataset; 'Low' = well-covered."
ws3.merge_cells("A3:G3")
apply_style(ws3["A3"], {
    "font": Font(name=FONT_NAME, size=10, italic=True, color="555555"),
    "alignment": Alignment(horizontal="left", vertical="center", wrap_text=True),
})
ws3.row_dimensions[3].height = 50

# Header
headers3 = ["NLP Task", "Papers in Urdu", "Maturity", "Notable Datasets", "Best Public?", "Gap Level", "Notes"]
for col, h in enumerate(headers3, 1):
    c = ws3.cell(row=5, column=col, value=h)
    apply_style(c, header_style())
ws3.row_dimensions[5].height = 36

# All unique tasks with counts
task_counts = Counter(p["task"] for p in PAPERS)

# For each task, list notable datasets
task_datasets = defaultdict(list)
task_public = defaultdict(list)
for p in PAPERS:
    if p["dataset"] and p["dataset"] != "N/A":
        task_datasets[p["task"]].append(p["dataset"])
        task_public[p["task"]].append(p["public"])

# All NLP tasks known in general (extensive list) - to identify zero-work tasks
ALL_KNOWN_NLP_TASKS = [
    "POS Tagging", "Morphology", "NER", "Chunking", "Parsing", "Coreference", "Anaphora",
    "Sentiment Analysis", "Emotion Detection", "Sarcasm", "Irony", "Humor",
    "Machine Translation", "Speech Translation", "Transliteration",
    "Text Classification", "Topic Modeling", "Topic Segmentation",
    "Summarization", "Abstractive Summarization", "Extractive Summarization",
    "Question Answering", "Question Generation", "MRC",
    "ASR", "TTS", "Speaker ID", "Speaker Diarization", "Speech Emotion", "Keyword Spotting",
    "Hate Speech", "Offensive Language", "Cyberbullying", "Profanity", "Toxicity",
    "Fake News", "Rumor Detection", "Misinformation", "Stance Detection", "Propaganda",
    "Clickbait", "Fact-checking",
    "Stemming", "Lemmatization", "Tokenization", "Sentence Boundary", "Spell Checking",
    "Word Embeddings", "Contextual Embeddings",
    "Information Retrieval", "Document Retrieval", "Passage Retrieval",
    "Information Extraction", "Relation Extraction", "Event Extraction", "Temporal Extraction",
    "Named Entity Linking", "Entity Disambiguation", "WSD",
    "Discourse Parsing", "RST Parsing", "Dialogue Acts",
    "Dialogue", "Chatbot", "Task-Oriented Dialogue",
    "LLM", "Instruction Tuning", "RLHF",
    "Code-mixed", "Code-switching", "Roman Urdu",
    "Cross-lingual", "Multilingual", "Transfer Learning",
    "Multimodal", "VQA", "Image Captioning", "Meme Classification",
    "OCR", "Handwritten Recognition",
    "Authorship", "Stylometry", "Plagiarism", "Readability", "Text Simplification",
    "Paraphrasing", "Semantic Similarity", "Natural Language Inference",
    "Keyword Extraction", "Keyphrase Generation", "Intent Classification",
    "Recommendation", "Clustering", "Language Modeling",
    "Negation", "Scope Detection",
    "SRL", "Semantic Role Labeling",
    "Sign Language", "Speech Recognition",
    "Lexicon", "WordNet", "Treebank", "Corpus",
    "Survey", "Bias/Fairness", "Language ID",
    "ABSA", "Aspect-based Sentiment",
]

# Maturity determination
def maturity(count):
    if count == 0: return "None"
    if count < 5: return "Small"
    if count < 15: return "Emerging"
    return "Mature"

def gap_level(task, count, datasets, public_list):
    if count == 0:
        return "Critical"
    if count < 5:
        # Check if datasets are public
        if any(p in ("Yes", "Partial") for p in public_list):
            return "High"
        return "Critical"
    if count < 15:
        if any(p in ("Yes", "Partial") for p in public_list):
            return "Medium"
        return "High"
    return "Low"

# Build task coverage rows
task_rows = []
seen_tasks = set()
for task in ALL_KNOWN_NLP_TASKS:
    if task in seen_tasks:
        continue
    seen_tasks.add(task)
    count = task_counts.get(task, 0)
    datasets = task_datasets.get(task, [])
    public_list = task_public.get(task, [])
    mat = maturity(count)
    gap = gap_level(task, count, datasets, public_list)
    notable_datasets = ", ".join(sorted(set(datasets))[:3]) if datasets else "—"
    best_public = "Yes" if any(p in ("Yes", "Partial") for p in public_list) else ("Request" if any(p == "Request" for p in public_list) else "No")
    notes = ""
    if count == 0:
        notes = "No Urdu work found in our search"
    elif count < 5:
        notes = f"Very limited Urdu work ({count} papers); small datasets"
    elif count < 15:
        notes = f"Growing area ({count} papers); datasets exist"
    else:
        notes = f"Active area ({count} papers); mature resources"
    task_rows.append((task, count, mat, notable_datasets, best_public, gap, notes))

# Add any tasks in our data that weren't in the ALL_KNOWN list
for task in task_counts:
    if task not in seen_tasks:
        seen_tasks.add(task)
        count = task_counts[task]
        datasets = task_datasets[task]
        public_list = task_public[task]
        mat = maturity(count)
        gap = gap_level(task, count, datasets, public_list)
        notable_datasets = ", ".join(sorted(set(datasets))[:3]) if datasets else "—"
        best_public = "Yes" if any(p in ("Yes", "Partial") for p in public_list) else ("Request" if any(p == "Request" for p in public_list) else "No")
        notes = f"Found {count} papers"
        task_rows.append((task, count, mat, notable_datasets, best_public, gap, notes))

# Sort by count desc
task_rows.sort(key=lambda x: (-x[1], x[0]))

# Write
for i, (task, count, mat, datasets, best_pub, gap, notes) in enumerate(task_rows):
    r = 6 + i
    bg = ALT_ROW if i % 2 == 0 else None
    # color code gap level
    gap_bg = {
        "Critical": GAP_CRITICAL,
        "High": GAP_HIGH,
        "Low": GAP_NONE,
        "Medium": None,
    }.get(gap, None)
    
    cells_data = [task, count, mat, datasets, best_pub, gap, notes]
    for col, v in enumerate(cells_data, 1):
        cell = ws3.cell(row=r, column=col, value=v)
        if col == 1:
            apply_style(cell, body_style(bold=True, color=PRIMARY, bg=bg))
        elif col == 2:
            apply_style(cell, body_style(align="center", bold=True, bg=bg))
        elif col == 3:
            mat_color = {"None": DANGER, "Small": WARNING, "Emerging": "FB8C00", "Mature": SUCCESS}.get(v, "000000")
            apply_style(cell, body_style(align="center", bold=True, color=mat_color, bg=bg))
        elif col == 5:
            pub_color = {"Yes": SUCCESS, "No": DANGER, "Request": WARNING, "Partial": "FB8C00"}.get(v, "000000")
            apply_style(cell, body_style(align="center", bold=True, color=pub_color, bg=bg))
        elif col == 6:
            apply_style(cell, body_style(align="center", bold=True, bg=gap_bg or bg))
        else:
            apply_style(cell, body_style(bg=bg))

# Column widths
widths3 = {1: 28, 2: 12, 3: 13, 4: 45, 5: 13, 6: 12, 7: 40}
for c, w in widths3.items():
    ws3.column_dimensions[get_column_letter(c)].width = w
ws3.freeze_panes = "A6"
ws3.auto_filter.ref = f"A5:G{5 + len(task_rows)}"

print(f"Sheet 3 (Task Coverage) done. {len(task_rows)} tasks listed.")

# Save what we have so far - we'll add sheets 4 and 5 next
wb.save("/home/z/my-project/download/Urdu_NLP_Research_Survey.xlsx")
print(f"\nIntermediate save successful.")
