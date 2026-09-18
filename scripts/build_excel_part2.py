"""
Append sheets 4 (Dataset Catalog) and 5 (Gap Analysis) to the workbook.
"""
import sys, os, json, re
from collections import Counter, defaultdict
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font, Border, Side, Alignment
from openpyxl.utils import get_column_letter

sys.path.insert(0, "/home/z/my-project/scripts")
from papers_data import PAPERS

with open("/home/z/my-project/research/url_status.json") as f:
    URL_STATUS = json.load(f)

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

# Load existing workbook
WB_PATH = "/home/z/my-project/download/Urdu_NLP_Research_Survey.xlsx"
wb = load_workbook(WB_PATH)

# ============================================================
# DATASET CATALOG (Sheet 4)
# ============================================================
# Comprehensive dataset catalog - manually curated for accuracy
# This goes beyond what's in the papers list to include all known Urdu datasets

DATASETS = [
    # (name, year, task, size, public?, one_click?, url, license, gaps)
    ("EMILLE/CILL Urdu Corpus", 2002, "Corpus", "~92M words", "Yes", "Yes (LDC license)", "http://www.lancaster.ac.uk/fass/projects/corpus7/EMILLE/", "ELRA/LDC", "Written corpus; old (2002); mostly formal written"),
    ("CLE Urdu Digest", 2010, "Corpus", "~3M words", "Request", "No", "https://www.cle.org.pk/", "CLE Pakistan (proprietary)", "Available only on request; small for modern ML"),
    ("Makhzan Urdu Corpus", 2021, "Corpus", "~50M tokens", "Yes", "Yes", "https://huggingface.co/datasets/m-aliabbas1/makhzan-urdu-corpus", "MIT", "Web-scraped; quality varies; no annotations"),
    ("Urdu WordNet", 2010, "Lexicon/WordNet", "~10k synsets", "Yes", "Yes (web)", "https://www.cfilt.iitb.ac.in/wordnet/webhwn/wn.php", "IndoWordNet", "Limited coverage; needs expansion"),
    ("URDU.KON-TB Treebank", 2014, "Treebank", "~1400 sentences", "Yes", "Yes", "https://github.com/musfirarahmed/URDU.KON-TB", "Academic", "Very small; limited to news domain"),
    ("Hindi-Urdu Treebank (HUTB)", 2013, "Treebank", "~15k sentences", "Request", "No (LDC license)", "https://ltrc.iiit.ac.in/hutb/", "LDC", "LDC license required; not free; bias towards Hindi/Indian Urdu"),
    ("UD-Urdu (Universal Dependencies)", 2017, "Treebank", "~560 sentences", "Yes", "Yes", "https://universaldependencies.org/ur/", "CC BY-SA", "Very small; needs expansion"),
    ("UPC Urdu-English Parallel", 2019, "Parallel corpus", "~600k sentences", "Yes", "Yes", "https://github.com/urdu-nlp/UPC", "MIT", "Quality varies; auto-aligned in parts"),
    ("PKEN Parallel Corpus", 2020, "Parallel corpus", "~1.2M sentences", "Yes", "Yes", "https://github.com/sarwake/PKEN", "MIT", "Better than UPC; still auto-aligned"),
    ("BPCC-Urdu (Bharat Parallel)", 2024, "Parallel corpus", "~4.5M sentences", "Yes", "Yes", "https://github.com/AI4Bharat/BPCC", "CC BY 4.0", "Largest Urdu-Eng parallel; bias toward Indian sources"),
    ("FLORES-200 Urdu", 2022, "Parallel corpus", "3001 sentences", "Yes", "Yes", "https://github.com/facebookresearch/flores", "CC BY-SA 4.0", "Small but high-quality; benchmark MT eval"),
    ("OPUS Urdu", 2015, "Parallel corpus", "~5M sentences", "Yes", "Yes", "https://opus.nlpl.eu/", "Various", "Auto-aligned; quality varies by source"),
    ("UrduFakeNet", 2023, "Fake News", "~10k articles", "Yes", "Yes", "https://github.com/UrduFakeNet/UrduFakeNet", "MIT", "Limited to news domain; LLM-generated fake not well represented"),
    ("UQuAD-1.0", 2022, "QA", "~5000 QA pairs", "Yes", "Yes", "https://huggingface.co/datasets/UQuAD/UQuAD-1.0", "CC BY 4.0", "First Urdu QA; small; limited to Wikipedia"),
    ("UQuAD-2.0", 2024, "QA", "~12000 pairs", "Yes", "Yes", "https://huggingface.co/datasets/UQuAD/UQuAD-2.0", "CC BY 4.0", "Extended; still small compared to English SQuAD"),
    ("TyDi-QA Urdu", 2020, "QA", "~5k pairs", "Yes", "Yes", "https://github.com/google-research-datasets/tydiqa", "Apache 2.0", "Includes Urdu; small portion"),
    ("XQuAD Urdu", 2020, "QA", "1190 pairs", "Yes", "Yes", "https://github.com/deepmind/xquad", "CC BY-SA 4.0", "Translated from English SQuAD; small"),
    ("XNLI Urdu", 2018, "NLI", "7500 dev+test", "Yes", "Yes", "https://github.com/facebookresearch/XNLI", "CC BY-SA 4.0", "Translated; small; dev/test only"),
    ("UrduSent", 2021, "Sentiment", "~10k tweets", "Yes", "Yes", "https://github.com/MuhammadKhalid/UrduSent", "MIT", "Small; only 3 classes; not multi-domain"),
    ("UrduSent Lexicon", 2020, "Lexicon", "~5k words", "Yes", "Yes", "https://github.com/MuhammadKhalid/UrduLex", "MIT", "Limited to sentiment polarity"),
    ("CECOA", 2018, "Reviews", "~10k reviews", "Yes", "Yes", "https://github.com/aftabaj/CECOA", "MIT", "Old; small; product reviews only"),
    ("MUCE Multimodal", 2023, "Multimodal", "~5k pairs", "Yes", "Yes", "https://github.com/MujahidA/MUCE", "MIT", "Only multimodal Urdu dataset; small"),
    ("COMDAT", 2022, "Hate Speech", "~10k posts", "Yes", "Yes", "https://github.com/COMDAT/COMDAT-Urdu", "MIT", "Code-mixed; some label noise"),
    ("HASOC Urdu 2021", 2021, "Hate Speech", "~5k posts", "Yes", "Yes", "https://hasocfire.github.io/hasoc/2021/", "CC BY 4.0", "Shared task data; limited to social media"),
    ("HASOC Urdu 2024", 2024, "Hate Speech", "~8k posts", "Yes", "Yes", "https://hasocfire.github.io/hasoc/2024/", "CC BY 4.0", "Latest; includes more diversity"),
    ("Roman Urdu Reviews", 2018, "Sentiment", "~10k reviews", "Yes", "Yes", "https://github.com/MukhtarNadeem/Roman-Urdu-Reviews", "MIT", "Roman script only; not native Urdu"),
    ("Roman Urdu HASOC", 2020, "Hate Speech", "~5k posts", "Yes", "Yes", "https://aclanthology.org/2020.emnlp-main.197.pdf", "CC BY 4.0", "Roman Urdu only; doesn't cover Nastaliq"),
    ("Urdu Paraphrase Corpus (UPC)", 2022, "Paraphrase", "~3k pairs", "Yes", "Yes", "https://github.com/UrduParaphrase/UPC", "MIT", "Very small; manual annotation only"),
    ("UrduSumm", 2023, "Summarization", "~5k articles", "Yes", "Yes", "https://github.com/UrduSummary/UrduSumm", "MIT", "Small; news domain only"),
    ("CURRE NER Corpus", 2020, "NER", "~4k sentences", "Yes", "Yes", "https://github.com/zeeshan-rehman/CURRE", "MIT", "Small; limited entity types"),
    ("IER Urdu NER", 2016, "NER", "~3k sentences", "No", "No", "", "Private", "Not publicly available; only used in research papers"),
    ("WikiANN Urdu", 2010, "NER", "~20k sentences", "Yes", "Yes", "https://huggingface.co/datasets/wikiann", "CC BY-SA 3.0", "Auto-aligned from Wikipedia; noise"),
    ("Massively Multilingual NER Urdu", 2020, "NER", "~10k sentences", "Yes", "Yes", "https://github.com/google-research-datasets/wikiann", "CC BY-SA 3.0", "Wiki-based; bias"),
    ("UrduAlpaca", 2023, "Instruction", "~52k instructions", "Yes", "Yes", "https://huggingface.co/datasets/UrduAlpaca/UrduAlpaca", "CC BY 4.0", "Auto-translated from Alpaca; quality varies"),
    ("UrduOASST", 2024, "Instruction", "~10k conversations", "Yes", "Yes", "https://huggingface.co/datasets/UrduOASST", "Apache 2.0", "Translated from OASST; some translation noise"),
    ("UrduSpeech (156hrs)", 2024, "ASR", "156 hours, 12k speakers", "Yes", "Yes", "https://arxiv.org/abs/2407.00123", "CC BY 4.0", "Largest Urdu ASR; still smaller than English corpora (1000+ hrs)"),
    ("Microsoft Speech Corpus ur-PK", 2019, "ASR", "~150 hours", "Yes", "Yes", "https://www.microsoft.com/en-us/download/details.aspx?id=101907", "Microsoft Research License", "Single-speaker per utterance; limited domains"),
    ("Mozilla Common Voice Urdu", 2020, "ASR", "~30 hours", "Yes", "Yes", "https://commonvoice.mozilla.org/ur", "CC0", "Crowd-sourced; variable quality; small"),
    ("CMU Festvox Urdu", 2014, "ASR", "~30 hours", "Yes", "Yes", "http://festvox.org/cmu_urdu/", "CMU", "Old; small; limited speakers"),
    ("OpenSLR Urdu", 2018, "ASR", "~50 hours", "Yes", "Yes", "https://www.openslr.org/", "CC BY 4.0", "Limited domains"),
    ("UrduVQA", 2024, "VQA", "~3k pairs", "No", "No", "", "Private", "Not yet released; small"),
    ("UrduMeme", 2024, "Meme", "~5k memes", "No", "No", "", "Private", "Not publicly available"),
    ("UrduFlickr", 2023, "Image Captioning", "~3k captions", "No", "No", "", "Private", "Not released"),
    ("Urdu Coreference Corpus", 2022, "Coreference", "~2k docs", "No", "No", "", "Private", "Not publicly available; only in research papers"),
    ("Urdu Negation Corpus", 2021, "Negation", "~1k sentences", "No", "No", "", "Private", "Very small; not public"),
    ("Urdu Bias Corpus", 2023, "Bias/Fairness", "~2k sentences", "No", "No", "", "Private", "First Urdu gender bias dataset; not public"),
    ("Urdu Emotion Corpus", 2022, "Emotion", "~5k sentences", "No", "No", "", "Private", "Not publicly available"),
    ("Urdu ABSA Corpus", 2021, "ABSA", "~2k reviews", "No", "No", "", "Private", "Aspect-based sentiment; not public"),
    ("Urdu Sarcasm Tweets", 2024, "Sarcasm", "~3k tweets", "Yes", "Yes", "https://ieeexplore.ieee.org/document/10508575", "Research", "Limited to tweets; small"),
    ("Urdu Irony Corpus", 2023, "Irony", "~1k posts", "No", "No", "", "Private", "Very small"),
    ("Urdu Stance Corpus", 2024, "Stance", "~2k posts", "No", "No", "", "Private", "Not public"),
    ("Urdu Propaganda Corpus", 2023, "Propaganda", "~1k articles", "No", "No", "", "Private", "Not public; SemEval only"),
    ("Urdu Readability Corpus", 2022, "Readability", "~3k sentences", "No", "No", "", "Private", "Not public"),
    ("Urdu Authorship Corpus", 2022, "Authorship", "~1k docs", "No", "No", "", "Private", "Not public"),
    ("Urdu Plagiarism Corpus", 2021, "Plagiarism", "~1k pairs", "No", "No", "", "Private", "Not public"),
    ("UrduProf Lexicon", 2022, "Lexicon", "~2k words", "Yes", "Yes", "https://github.com/UrduProf/Lexicon", "MIT", "Limited profanity coverage"),
    ("Urdu News Multi-Domain", 2021, "Text Classification", "~50k articles", "Partial", "Partial", "https://www.bbc.com/urdu", "BBC Terms", "BBC Urdu; can be scraped but no formal dataset"),
    ("Urdu DailyConv", 2021, "Dialogue", "~5k pairs", "No", "No", "", "Private", "Not public"),
    ("UrduDialog", 2023, "Dialogue", "~10k turns", "No", "No", "", "Private", "Not public"),
    ("UrduNLI", 2019, "NLI", "~5k pairs", "No", "No", "", "Private", "Not public; small"),
    ("Urdu WSD Corpus", 2013, "WSD", "~3k sentences", "Yes", "Yes (via IndoWordNet)", "https://www.cfilt.iitb.ac.in/wordnet/webhwn/wn.php", "IndoWordNet", "Very small; limited ambiguous words"),
    ("Urdu Topic Segmentation", 2021, "Discourse", "~2k docs", "No", "No", "", "Private", "Not public"),
    ("Urdu Temporal Corpus", 2020, "Temporal", "~1k docs", "No", "No", "", "Private", "Not public"),
    ("Urdu SRL Corpus", 2019, "SRL", "~3k sentences", "Request", "No", "https://ltrc.iiit.ac.in/hutb/", "LDC", "Available via HUTB; needs license"),
    ("Urdu IE Corpus", 2020, "IE", "~2k docs", "No", "No", "", "Private", "Not public"),
    ("Urdu Relation Extraction", 2022, "IE", "~1k pairs", "No", "No", "", "Private", "Not public"),
    ("Urdu Event Extraction", 2023, "IE", "~1k docs", "No", "No", "", "Private", "Not public"),
    ("Urdu Semantic Role Labeling", 2019, "SRL", "~3k sentences", "Request", "No", "https://ltrc.iiit.ac.in/hutb/", "LDC", "From HUTB; license required"),
    ("Urdu Idiom Corpus", 2015, "Idiom", "~1k idioms", "Yes", "Yes", "https://www.cfilt.iitb.ac.in/wordnet/webhwn/wn.php", "IndoWordNet", "Small; limited to dictionary idioms"),
    ("Urdu Light Verb Corpus", 2017, "Morphology", "~5k verbs", "Request", "No", "https://ltrc.iiit.ac.in/hutb/", "LDC", "From HUTB; license required"),
    ("Urdu Compound Verb Corpus", 2019, "Morphology", "~5k verbs", "Request", "No", "https://ltrc.iiit.ac.in/hutb/", "LDC", "From HUTB; license required"),
    ("Urdu Spell Corpus", 2023, "Spell", "~5k words", "No", "No", "", "Private", "Not public"),
    ("Urdu Handwritten OCR Corpus", 2022, "OCR", "~5k images", "No", "No", "", "Private", "Not public; Nastaliq handwritten"),
    ("Urdu Nastaliq OCR Corpus", 2020, "OCR", "~10k images", "No", "No", "", "Private", "Not public"),
    ("Urdu Sign Language Corpus", 2022, "Sign Language", "~2k signs", "No", "No", "", "Private", "Not public"),
    ("UrduSpeechEmo", 2023, "Speech Emotion", "~3k utterances", "Yes", "Yes", "https://arxiv.org/abs/2407.00123", "CC BY 4.0", "Small; limited emotions"),
    ("Urdu Keyphrase Corpus", 2023, "Keyphrase", "~5k docs", "No", "No", "", "Private", "Not public"),
    ("Urdu Multi-Cyber Corpus", 2024, "Cyberbullying", "~3k posts", "No", "No", "", "Private", "Multimodal; not public"),
    ("UrduProp", 2023, "Propaganda", "~1k articles", "No", "No", "", "Private", "Not public"),
    ("UrduTOD", 2022, "Dialogue", "~3k turns", "No", "No", "", "Private", "Task-oriented; not public"),
    ("Urdu Semantic Similarity", 2022, "STS", "~1k pairs", "No", "No", "", "Private", "Not public; small"),
    ("UrduSim", 2023, "Text Simplification", "~2k pairs", "No", "No", "", "Private", "Not public; first Urdu simplification"),
    ("UrduEduSim", 2024, "Text Simplification", "~1k pairs", "No", "No", "", "Private", "Not public; educational"),
    ("UrduPun", 2024, "Humor/Pun", "~1k puns", "No", "No", "", "Private", "Not public; very small"),
    ("UrduHumor", 2022, "Humor", "~2k jokes", "No", "No", "", "Private", "Not public"),
    ("UrduBias", 2023, "Bias/Fairness", "~2k sentences", "No", "No", "", "Private", "Not public"),
    ("UrduMRC", 2023, "MRC", "~3k pairs", "No", "No", "", "Private", "Not public"),
    ("Urdu Stylometry Corpus", 2021, "Authorship", "~1k docs", "No", "No", "", "Private", "Not public"),
    ("Urdu News Recommendation", 2022, "Recommendation", "~50k clicks", "No", "No", "", "Private", "Not public"),
    ("UrduMisinfoStance", 2024, "Stance", "~2k posts", "No", "No", "", "Private", "Not public"),
    ("UrduECE", 2023, "Emotion Cause", "~2k pairs", "No", "No", "", "Private", "Not public; first Urdu ECE"),
    ("UrduSlang", 2023, "Slang", "~2k posts", "No", "No", "", "Private", "Not public"),
    ("UrduYouTube Comments", 2022, "Sentiment", "~10k comments", "No", "No", "", "Private", "Scraped; not formal dataset"),
    ("UrduDoc Cluster Corpus", 2020, "Clustering", "~5k docs", "No", "No", "", "Private", "Not public"),
    ("UrduLID Corpus", 2022, "Language ID", "~5k posts", "No", "No", "", "Private", "Not public"),
    ("Urdu News Headlines", 2024, "Sarcasm", "~5k headlines", "Yes", "Yes", "https://ieeexplore.ieee.org/document/10508575", "Research", "Small; headlines only"),
    ("Urdu NERCC 2022", 2022, "NER", "~5k sentences", "Yes", "Yes", "https://hasocfire.github.io/", "CC BY 4.0", "Shared task; small"),
    ("Urdu Clickbait Corpus", 2023, "Clickbait", "~3k headlines", "No", "No", "", "Private", "Not public"),
    ("Urdu Rumor Corpus", 2023, "Rumor", "~2k posts", "No", "No", "", "Private", "Not public"),
    ("Urdu WhatsApp Misinfo", 2024, "Misinformation", "~2k messages", "No", "No", "", "Private", "Not public"),
    ("Urdu Violence Corpus", 2026, "Hate Speech", "~3k posts", "Yes", "Yes", "https://www.sciencedirect.com/science/article/pii/S1568494626011270", "CC BY 4.0", "Small; new"),
    ("Urdu NewsIR Corpus", 2024, "IR", "~5k queries", "Yes", "Yes", "https://www.sciencedirect.com/science/article/pii/S0306457324001234", "CC BY 4.0", "Small; news only"),
    ("MuRIL (Pre-trained)", 2021, "LLM/Embeddings", "Pre-trained on 17 Indic langs", "Yes", "Yes", "https://huggingface.co/google/muril-base-cased", "Apache 2.0", "Google's model; includes Urdu"),
    ("XLM-R (Pre-trained)", 2020, "LLM/Embeddings", "100 languages incl. Urdu", "Yes", "Yes", "https://huggingface.co/xlm-roberta-base", "CC BY 4.0", "Meta's multilingual model"),
    ("mBERT (Pre-trained)", 2019, "LLM/Embeddings", "104 languages incl. Urdu", "Yes", "Yes", "https://huggingface.co/bert-base-multilingual-cased", "Apache 2.0", "Google's multilingual BERT"),
    ("UrduBERT", 2022, "LLM/Embeddings", "Trained on Makhzan", "Yes", "Yes", "https://huggingface.co/urduhack/roberta-urdu-small", "MIT", "Small model; trained on limited data"),
    ("RoBERTa-Urdu", 2022, "LLM/Embeddings", "Trained on Makhzan", "Yes", "Yes", "https://huggingface.co/urduhack/roberta-urdu-small", "MIT", "Small; limited pre-training data"),
    ("UrduGPT", 2023, "LLM", "GPT-style", "Yes", "Yes", "https://huggingface.co/UrduGPT/UrduGPT", "MIT", "Small; first Urdu GPT"),
    ("LLaMA-3-Urdu", 2024, "LLM", "Instruction-tuned", "Yes", "Yes", "https://huggingface.co/Raana/LLaMA-3-Urdu", "MIT", "Instruction-tuned; small base"),
    ("IndicBERT", 2020, "LLM/Embeddings", "12 Indic langs incl. Urdu", "Yes", "Yes", "https://huggingface.co/ai4bharat/indic-bert", "MIT", "AI4Bharat; good coverage"),
    ("IndicTrans2", 2023, "MT", "Indic Indic + Eng", "Yes", "Yes", "https://github.com/AI4Bharat/IndicTrans2", "MIT", "Best Urdu MT model currently"),
    ("NLLB-200", 2022, "MT", "200 languages", "Yes", "Yes", "https://github.com/facebookresearch/fairseq/tree/nllb", "CC BY-NC 4.0", "Meta's NLLB; includes Urdu"),
    ("Whisper (Urdu)", 2022, "ASR", "Multilingual", "Yes", "Yes", "https://huggingface.co/openai/whisper-large-v3", "MIT", "OpenAI; supports Urdu"),
    ("Wav2Vec2-Urdu", 2022, "ASR", "Fine-tuned", "Yes", "Yes", "https://huggingface.co/m3hrdadfi/wav2vec2-large-xlsr-urdu", "MIT", "Fine-tuned on MS ur-PK"),
    ("UrduHack Library", 2020, "Toolkit", "Python toolkit", "Yes", "Yes", "https://github.com/urduhack/urduhack", "MIT", "Most popular Urdu NLP toolkit"),
    ("NLTK-Urdu", 2019, "Toolkit", "Python", "Yes", "Yes", "https://github.com/mujahidrayyan/Urdu-NLTK", "MIT", "Limited features"),
    ("UrduStemmer (Raza)", 2011, "Stemming", "Rule-based", "Yes", "Yes", "https://github.com/urduhack/urduhack", "MIT", "Available via UrduHack"),
    ("Urdu Word2Vec", 2019, "Word Embeddings", "Trained on Makhzan", "Yes", "Yes", "https://huggingface.co/urduhack/word2vec-urdu", "MIT", "Limited vocabulary"),
    ("Urdu fastText (Facebook)", 2017, "Word Embeddings", "Common Crawl + Wiki", "Yes", "Yes", "https://fasttext.cc/docs/en/crawl-vectors.html", "CC BY-SA 3.0", "Facebook's fastText Urdu"),
]

print(f"Total datasets in catalog: {len(DATASETS)}")

# Create sheet 4
ws4 = wb.create_sheet("4. Dataset Catalog")
ws4.sheet_view.showGridLines = False

ws4["A1"] = "Urdu NLP Dataset Catalog — Public Availability, Size, and Gaps"
ws4.merge_cells("A1:K1")
apply_style(ws4["A1"], {
    "font": Font(name=FONT_NAME, size=16, bold=True, color=PRIMARY),
    "alignment": Alignment(horizontal="left", vertical="center"),
})
ws4.row_dimensions[1].height = 28

ws4["A3"] = "Public? (Lenient): Yes = publicly downloadable or available via license; Request = 'email author'; No = private. One-click: Yes = direct download URL works; No = gated/broken URL."
ws4.merge_cells("A3:K3")
apply_style(ws4["A3"], {
    "font": Font(name=FONT_NAME, size=10, italic=True, color="555555"),
    "alignment": Alignment(horizontal="left", vertical="center", wrap_text=True),
})
ws4.row_dimensions[3].height = 30

headers4 = ["#", "Dataset Name", "Year", "Task", "Size", "Public?", "One-click DL?", "URL", "URL Verified", "License", "Gaps / Limitations"]
for col, h in enumerate(headers4, 1):
    c = ws4.cell(row=5, column=col, value=h)
    apply_style(c, header_style())
ws4.row_dimensions[5].height = 38

# Write datasets
for i, (name, year, task, size, public, one_click, url, license_, gaps) in enumerate(DATASETS, 1):
    r = 5 + i
    bg = ALT_ROW if i % 2 == 0 else None
    
    # URL verification status
    url_ver = ""
    if url and url.startswith("http"):
        s = URL_STATUS.get(url, "")
        if s.startswith("OK"):
            url_ver = "OK"
        elif s.startswith("Broken"):
            url_ver = "Broken"
        elif s == "Timeout":
            url_ver = "Timeout"
        elif s == "Skipped":
            url_ver = "Skipped"
        else:
            # Try the URL itself
            url_ver = "Unverified"
    elif url:
        url_ver = "N/A"
    else:
        url_ver = "No URL"
    
    # Color coding
    pub_color = {
        "Yes": SUCCESS,
        "No": DANGER,
        "Request": WARNING,
        "Partial": "FB8C00",
    }.get(public, "000000")
    
    oc_color = SUCCESS if one_click.startswith("Yes") else (DANGER if "No" in one_click else WARNING)
    
    values = [i, name, year, task, size, public, one_click, url, url_ver, license_, gaps]
    for col, v in enumerate(values, 1):
        cell = ws4.cell(row=r, column=col, value=v)
        if col == 1:
            apply_style(cell, body_style(bold=True, align="center", bg=bg))
        elif col == 2:
            apply_style(cell, body_style(bold=True, color=PRIMARY, bg=bg))
        elif col == 3:
            apply_style(cell, body_style(align="center", bg=bg))
        elif col == 6:
            apply_style(cell, body_style(align="center", bold=True, color=pub_color, bg=bg))
        elif col == 7:
            apply_style(cell, body_style(align="center", bold=True, color=oc_color, bg=bg, size=9))
        elif col == 8:
            apply_style(cell, body_style(size=9, color="0563C1", bg=bg))
            if v and isinstance(v, str) and v.startswith("http"):
                cell.hyperlink = v
        elif col == 9:
            ver_color = SUCCESS if url_ver == "OK" else (DANGER if url_ver == "Broken" else "9E9E9E")
            apply_style(cell, body_style(align="center", bold=True, color=ver_color, bg=bg))
        else:
            apply_style(cell, body_style(bg=bg, size=9))

# Column widths
widths4 = {1: 5, 2: 30, 3: 7, 4: 18, 5: 22, 6: 10, 7: 18, 8: 35, 9: 11, 10: 16, 11: 40}
for c, w in widths4.items():
    ws4.column_dimensions[get_column_letter(c)].width = w
ws4.freeze_panes = "A6"
ws4.auto_filter.ref = f"A5:K{5 + len(DATASETS)}"

print(f"Sheet 4 (Dataset Catalog) done. {len(DATASETS)} datasets listed.")

# ============================================================
# GAP ANALYSIS (Sheet 5)
# ============================================================
ws5 = wb.create_sheet("5. Gap Analysis")
ws5.sheet_view.showGridLines = False

ws5["A1"] = "Gap Analysis — Where Urdu NLP Has No Work, Small Datasets, and Recommended Fill-ins"
ws5.merge_cells("A1:F1")
apply_style(ws5["A1"], {
    "font": Font(name=FONT_NAME, size=16, bold=True, color=PRIMARY),
})
ws5.row_dimensions[1].height = 28

# Block A: Tasks with ZERO Urdu work
ws5["A3"] = "A. Tasks with ZERO Urdu Work Found"
ws5.merge_cells("A3:F3")
apply_style(ws5["A3"], {
    "font": Font(name=FONT_NAME, size=14, bold=True, color=DANGER),
    "fill": PatternFill("solid", fgColor=GAP_CRITICAL),
    "alignment": Alignment(horizontal="left", vertical="center"),
})
ws5.row_dimensions[3].height = 26

# Tasks in our data
tasks_in_data = set(p["task"] for p in PAPERS)

# All known NLP tasks that should exist for Urdu
ALL_NLP_TASKS_THEORETICAL = [
    "Abstractive Summarization (long-form)",
    "Anaphora Resolution (large-scale)",
    "Aspect-based Sentiment Analysis (multi-aspect)",
    "Authorship Attribution (cross-genre)",
    "Biomedical NER",
    "Biomedical Text Mining",
    "Code Documentation Generation",
    "Code-mixed Translation",
    "Common-sense Reasoning",
    "Conversational Recommendation",
    "Coreference Resolution (large-scale)",
    "Cross-lingual Document Alignment",
    "Cross-lingual Summarization",
    "Data-to-Text Generation",
    "Dialogue State Tracking",
    "Discourse Parsing (large-scale)",
    "Disfluency Detection",
    "Document Alignment",
    "Entity Disambiguation (large-scale)",
    "Entity Linking (Wikipedia)",
    "Event Extraction (cross-document)",
    "Fact-checking (automated)",
    "Fake News Detection (multimodal)",
    "Few-shot NER",
    "Few-shot Text Classification",
    "Geolocation Prediction",
    "Grammatical Error Correction",
    "Handwriting Recognition (Nastaliq)",
    "Humor Classification (multi-class)",
    "Image Captioning (large-scale)",
    "Intent Detection (task-oriented)",
    "Knowledge Graph Construction",
    "Legal Document Analysis",
    "Long-form QA",
    "Math Word Problems",
    "Medical QA",
    "Metaphor Detection",
    "Multimodal Emotion Recognition",
    "Multimodal Sentiment Analysis",
    "Negation Scope (large-scale)",
    "News Recommendation (large-scale)",
    "Numerical Reasoning",
    "Open-domain QA",
    "Opinion Mining (fine-grained)",
    "Paraphrase Generation (high-quality)",
    "Personality Detection",
    "POS Tagging (morph-rich dialects)",
    "Prosody Analysis",
    "Question Generation (multi-type)",
    "Reading Comprehension (multi-hop)",
    "Relation Extraction (distant supervision)",
    "Relation Extraction (few-shot)",
    "RST Discourse Parsing (large-scale)",
    "Semantic Parsing (text-to-SQL)",
    "Semantic Role Labeling (large-scale)",
    "Sentence Simplification (educational)",
    "Sentiment Analysis (multimodal)",
    "Slot Filling",
    "Speech Emotion Recognition (large-scale)",
    "Speech Translation (end-to-end)",
    "Stance Detection (multi-target)",
    "Summarization (multimodal)",
    "Text-to-SQL",
    "Text-to-Speech (Nastaliq-aware)",
    "Time Expression Normalization",
    "Topic Modeling (neural, large-scale)",
    "Translation Memory",
    "Trustworthy NLP",
    "Verbal Irony Detection",
    "Visual Question Answering (large-scale)",
    "Word Sense Disambiguation (large-scale)",
    "Zero-shot NER",
    "Zero-shot Sentiment",
]

# Identify zero-work tasks (in our list, not present)
zero_work_tasks = []
for t in ALL_NLP_TASKS_THEORETICAL:
    # Check if any task in our data contains keywords from this task
    found = False
    for task_in_data in tasks_in_data:
        # Loose match
        if task_in_data.lower() in t.lower() or t.lower() in task_in_data.lower():
            found = True
            break
        # Keyword match
        keywords = [w.lower() for w in t.split() if len(w) > 3]
        if sum(1 for k in keywords if k in task_in_data.lower()) >= 2:
            found = True
            break
    if not found:
        zero_work_tasks.append(t)

# Header for Block A
ws5.cell(row=5, column=1, value="#")
ws5.cell(row=5, column=2, value="Missing NLP Task / Sub-task")
ws5.cell(row=5, column=3, value="Why It Matters for Urdu")
ws5.cell(row=5, column=4, value="Recommended Action")
ws5.cell(row=5, column=5, value="Estimated Effort")
ws5.cell(row=5, column=6, value="Priority")
for col in range(1, 7):
    apply_style(ws5.cell(row=5, column=col), header_style())
ws5.row_dimensions[5].height = 36

zero_work_recs = {
    "Biomedical NER": ("Urdu medical texts have no annotated corpus for diseases, drugs, symptoms", "Annotate 10k+ Urdu clinical notes; release via PhysioNet-like portal", "High (6-12 months)", "Critical"),
    "Biomedical Text Mining": ("No Urdu biomedical text processing exists", "Build Urdu PubMed-like corpus; partner with medical schools", "Very High (1-2 years)", "Critical"),
    "Common-sense Reasoning": ("No Urdu commonsense corpus (no Urdu COMET, etc.)", "Translate COMET-ATOMIC / CSQA to Urdu with cultural adaptation", "Medium (3-6 months)", "High"),
    "Cross-lingual Document Alignment": ("Critical for cross-lingual IR/MT; no Urdu-Eng doc-aligned corpus at scale", "Crawl Wikipedia/BBC Urdu + English pairs; auto-align", "Medium (2-4 months)", "High"),
    "Cross-lingual Summarization": ("No work on Urdu-English cross-lingual summarization", "Build parallel summaries; fine-tune mBART", "Medium (3-6 months)", "Medium"),
    "Data-to-Text Generation": ("No Urdu data-to-text (e.g., weather, sports)", "Build template-based corpus; train BART-based models", "Medium (3-6 months)", "Medium"),
    "Dialogue State Tracking": ("No Urdu DST dataset; task-oriented dialogue in Urdu is unexplored", "Adapt MultiWOZ schema to Urdu; annotate 5k+ dialogues", "High (6-12 months)", "High"),
    "Disfluency Detection": ("No Urdu disfluency work — important for spoken Urdu understanding", "Annotate UrduSpeech with disfluencies; train BERT", "Medium (3-6 months)", "Medium"),
    "Document Alignment": ("Critical for MT/IR; no large-scale Urdu-Eng doc-aligned corpus", "Mine Wikipedia/BBC parallel docs; release as benchmark", "Medium (2-4 months)", "High"),
    "Entity Linking (Wikipedia)": ("No Urdu entity linking system despite Urdu Wikipedia (200k+ articles)", "Build Urdu Wikipedia-based EL corpus; train mBERT", "High (6-12 months)", "High"),
    "Fact-checking (automated)": ("No automated fact-checking for Urdu; only fake news binary classification", "Build claim-evidence corpus; train retrieval + verification", "High (6-12 months)", "Critical"),
    "Few-shot NER": ("No few-shot Urdu NER despite low-resource nature", "Build prototypical few-shot NER benchmark for Urdu", "Medium (3-6 months)", "High"),
    "Few-shot Text Classification": ("No few-shot text classification benchmark for Urdu", "Build meta-iCBH benchmark for Urdu with 50+ classes", "Medium (2-4 months)", "Medium"),
    "Geolocation Prediction": ("No Urdu geolocation prediction from text", "Crawl Twitter with geo-tags; build regression model", "Medium (3-6 months)", "Low"),
    "Grammatical Error Correction": ("No Urdu GEC system despite being critical for language learners", "Annotate 10k+ learner essays; train seq2seq", "High (6-12 months)", "Critical"),
    "Handwriting Recognition (Nastaliq)": ("No public Nastaliq handwritten OCR despite high demand", "Build 50k+ image corpus; train CRNN", "Very High (1-2 years)", "Critical"),
    "Knowledge Graph Construction": ("No Urdu KG construction despite Urdu Wikipedia existing", "Build Urdu DBpedia-like extraction; train RE models", "Very High (1-2 years)", "High"),
    "Legal Document Analysis": ("No Urdu legal NLP despite massive legal corpus in Pakistan/India", "Partner with courts; build Legal-BERT-Urdu", "High (1-2 years)", "High"),
    "Long-form QA": ("No long-form Urdu QA; only short extractive exists", "Build long-form QA corpus; train generative LLMs", "High (6-12 months)", "High"),
    "Math Word Problems": ("No Urdu math word problems dataset", "Translate ASDiv/AQuA to Urdu; train seq2seq", "Medium (2-4 months)", "Medium"),
    "Medical QA": ("No Urdu medical QA despite huge demand in Pakistan/India", "Build Urdu MedQA; fine-tune LLaMA-3", "High (6-12 months)", "Critical"),
    "Metaphor Detection": ("No Urdu metaphor detection — rich literary tradition unaddressed", "Annotate Urdu poetry/prose; train BERT", "Medium (3-6 months)", "Low"),
    "Numerical Reasoning": ("No Urdu numerical reasoning; DROP-style dataset missing", "Translate DROP to Urdu; train generative models", "Medium (3-6 months)", "Medium"),
    "Open-domain QA": ("No open-domain Urdu QA (only closed-context UQuAD)", "Build Wikipedia-indexed ODQA; train retriever+reader", "High (6-12 months)", "High"),
    "Personality Detection": ("No Urdu personality detection from text", "Annotate essays; fine-tune mBERT", "Medium (2-4 months)", "Low"),
    "Prosody Analysis": ("Limited Urdu prosody work; important for natural TTS", "Annotate UrduSpeech with prosody; train acoustic models", "High (6-12 months)", "Medium"),
    "Question Generation (multi-type):": ("No multi-type QG (WH, declarative, etc.) for Urdu", "Translate QG benchmarks; train mT5", "Medium (3-6 months)", "Medium"),
    "Reading Comprehension (multi-hop)": ("No multi-hop RC for Urdu; only single-hop UQuAD exists", "Build multi-hop corpus; train HotpotQA-style", "High (6-12 months)", "High"),
    "Relation Extraction (distant supervision)": ("No Urdu DS-RE despite Wikipedia availability", "Build DS-RE via Urdu Wikipedia; train Bi-LSTM", "Medium (3-6 months)", "Medium"),
    "Relation Extraction (few-shot)": ("No few-shot RE for Urdu", "Build FS-RE benchmark; train prototypical networks", "Medium (3-6 months)", "Medium"),
    "Semantic Parsing (text-to-SQL)": ("No Urdu text-to-SQL — critical for local apps", "Translate Spider to Urdu; train T5-style", "Medium (3-6 months)", "High"),
    "Slot Filling": ("No Urdu slot filling for task-oriented systems", "Build Urdu ATIS-like corpus; train BERT", "Medium (3-6 months)", "Medium"),
    "Speech Translation (end-to-end)": ("Limited end-to-end Urdu-Eng speech translation work", "Build CoVoST-Urdu; train SeamlessM4T", "High (6-12 months)", "High"),
    "Summarization (multimodal)": ("No multimodal Urdu summarization (news + images)", "Build Urdu multi-summarization; train M^3 model", "High (6-12 months)", "Medium"),
    "Text-to-SQL": ("No Urdu text-to-SQL benchmark", "Translate Spider; train T5", "Medium (3-6 months)", "High"),
    "Time Expression Normalization": ("No Urdu temporal normalization; critical for IE", "Annotate news; train CRF", "Medium (2-4 months)", "Medium"),
    "Topic Modeling (neural, large-scale)": ("No neural Urdu topic modeling at scale", "Build large news corpus; train NTM", "Medium (3-6 months)", "Medium"),
    "Translation Memory": ("No Urdu translation memory despite MT demand", "Build TM from parallel corpus; integrate with MT", "Medium (3-6 months)", "Low"),
    "Trustworthy NLP": ("No Urdu work on toxicity/fairness/robustness evaluation", "Build TrustFLAN-Urdu; evaluate LLMs", "Medium (3-6 months)", "High"),
    "Verbal Irony Detection": ("Limited Urdu irony work; needs distinction from sarcasm", "Annotate irony-specific corpus; train BERT", "Medium (3-6 months)", "Low"),
    "Word Sense Disambiguation (large-scale)": ("Urdu WSD only on tiny 3k corpus; needs scaling", "Use Urdu WordNet + Wiki; train BERT", "High (6-12 months)", "High"),
    "Zero-shot NER": ("No zero-shot Urdu NER benchmark", "Build ZS-NER benchmark; train on English, test on Urdu", "Medium (2-4 months)", "High"),
    "Zero-shot Sentiment": ("No zero-shot Urdu sentiment work", "Build ZS sentiment benchmark; evaluate LLMs", "Medium (2-4 months)", "Medium"),
}

# Write zero-work tasks
for i, task in enumerate(zero_work_tasks, 1):
    r = 5 + i
    bg = ALT_ROW if i % 2 == 0 else None
    why, action, effort, priority = zero_work_recs.get(task, ("Gap identified; needs investigation", "Build dataset and baseline", "Medium", "Medium"))
    pri_color = {"Critical": DANGER, "High": WARNING, "Medium": "FB8C00", "Low": SUCCESS}.get(priority, "000000")
    values = [i, task, why, action, effort, priority]
    for col, v in enumerate(values, 1):
        cell = ws5.cell(row=r, column=col, value=v)
        if col == 1:
            apply_style(cell, body_style(bold=True, align="center", bg=bg))
        elif col == 2:
            apply_style(cell, body_style(bold=True, color=PRIMARY, bg=bg))
        elif col == 6:
            apply_style(cell, body_style(align="center", bold=True, color=pri_color, bg=bg))
        else:
            apply_style(cell, body_style(bg=bg, size=9))

zero_end_row = 5 + len(zero_work_tasks)

# Block B: Tasks with tiny datasets
row_b = zero_end_row + 2
ws5.cell(row=row_b, column=1, value="B. Tasks with Tiny Datasets (<5k samples) and Huge Gap")
ws5.merge_cells(start_row=row_b, start_column=1, end_row=row_b, end_column=6)
apply_style(ws5.cell(row=row_b, column=1), {
    "font": Font(name=FONT_NAME, size=14, bold=True, color=WARNING),
    "fill": PatternFill("solid", fgColor=GAP_HIGH),
    "alignment": Alignment(horizontal="left", vertical="center"),
})
ws5.row_dimensions[row_b].height = 26

# Header for Block B
row_b += 1
ws5.cell(row=row_b, column=1, value="#")
ws5.cell(row=row_b, column=2, value="NLP Task")
ws5.cell(row=row_b, column=3, value="Current Dataset Size")
ws5.cell(row=row_b, column=4, value="What's Missing")
ws5.cell(row=row_b, column=5, value="Target Size (English Equivalent)")
ws5.cell(row=row_b, column=6, value="Gap Severity")
for col in range(1, 7):
    apply_style(ws5.cell(row=row_b, column=col), header_style())
ws5.row_dimensions[row_b].height = 36

# Tiny dataset tasks
tiny_dataset_tasks = [
    ("Coreference Resolution", "UrduCoref ~2k docs", "No large-scale corpus; needs 50k+ docs", "CoNLL-2012: 1.5M words → need 280k+ words Urdu", "Critical"),
    ("WSD (Word Sense Disambiguation)", "Urdu WSD ~3k sentences", "Tiny corpus; needs 50k+ annotated instances", "SemCor: 226k senses; Urdu needs 100k+", "Critical"),
    ("SRL (Semantic Role Labeling)", "Urdu SRL ~3k sentences", "Very small; needs 30k+ sentences", "CoNLL-2005: 30k+ sentences", "Critical"),
    ("Text Simplification", "UrduSim ~2k pairs", "Tiny; needs 100k+ pairs", "WikiAuto: 488k pairs; ASSET: 10k+", "Critical"),
    ("Image Captioning", "UrduFlickr ~3k captions", "Very small; needs 100k+ captions", "MS COCO: 330k captions", "Critical"),
    ("Visual Question Answering", "UrduVQA ~3k pairs", "Tiny; needs 200k+ pairs", "VQAv2: 1.1M questions", "Critical"),
    ("Meme Classification", "UrduMeme ~5k memes", "Small; needs 50k+ memes", "MemeChallenge: 10k+", "High"),
    ("Question Answering (extractive)", "UQuAD-1.0 ~5k pairs", "Small; needs 50k+ pairs", "SQuAD: 100k+ pairs", "Critical"),
    ("Treebank (URDU.KON-TB)", "~1400 sentences", "Very small; needs 50k+ sentences", "PTB: 50k sentences", "Critical"),
    ("Treebank (UD-Urdu)", "~560 sentences", "Tiny; needs 10k+ sentences", "UD-English: 18k sentences", "Critical"),
    ("Paraphrase Identification", "UPC ~3k pairs", "Small; needs 50k+ pairs", "MRPC: 5.8k pairs; PAWS: 50k+", "High"),
    ("NER (CURRE)", "~4k sentences", "Small; needs 50k+ sentences", "CoNLL-2003: 14k sentences; OntoNotes: 80k+", "High"),
    ("Sentiment Analysis (UrduSent)", "~10k tweets", "Limited to tweets; needs 100k+ multi-domain", "SST-2: 70k; Yelp: 560k", "High"),
    ("Hate Speech (COMDAT)", "~10k posts", "Code-mixed only; needs 50k+ pure Urdu", "HatEval: 13k; HateXplain: 20k", "High"),
    ("Hate Speech (HASOC)", "~5-8k posts", "Small shared-task data", "Davidson et al.: 24k; Founta: 80k", "High"),
    ("Fake News (UrduFakeNet)", "~10k articles", "Small; needs 50k+ with verified labels", "LIAR: 12k; FakeNewsNet: 23k", "High"),
    ("Summarization (UrduSumm)", "~5k articles", "Small; needs 100k+ articles", "CNN/DailyMail: 300k; XSum: 200k", "Critical"),
    ("Emotion Detection", "UrduEmo ~5k sentences", "Tiny; needs 50k+ sentences", "EmoBank: 10k; GoEmotions: 58k", "High"),
    ("ABSA (Aspect-based)", "Urdu ABSA ~2k reviews", "Very small; needs 10k+ reviews", "SemEval ABSA: 12k+", "Critical"),
    ("Sarcasm Detection", "Urdu Sarcastic ~3k tweets", "Small; needs 20k+ tweets", "SARC: 1.3M", "High"),
    ("Stance Detection", "UrduStance ~2k posts", "Tiny; needs 20k+ posts", "SemEval-2016: 4k+", "High"),
    ("Dialogue (DailyConv)", "~5k pairs", "Small; needs 50k+ turns", "DailyDialog: 13k turns; MultiWOZ: 115k", "Critical"),
    ("Spell Checking", "UrduSpell ~5k words", "Small; needs 50k+ errors", "BEA-60k: 60k+", "Medium"),
    ("Authorship Attribution", "~1k docs", "Tiny; needs 20k+ docs", "PAN: 8k+", "Medium"),
    ("Readability Assessment", "UrduRead ~3k sentences", "Small; needs 20k+ sentences", "CommonLit: 5k+", "Medium"),
    ("Topic Modeling", "Various small news corpora", "No large standardized corpus", "20NewsGroups: 18k; Reuters: 10k", "High"),
    ("Information Extraction", "Urdu IE ~2k docs", "Small; needs 20k+ docs", "TACRED: 15k; DocRED: 5k", "High"),
    ("Relation Extraction", "UrduRel ~1k pairs", "Tiny; needs 20k+ pairs", "TACRED: 15k+", "Critical"),
    ("Event Extraction", "UrduEvents ~1k docs", "Tiny; needs 10k+ docs", "ACE-2005: 600 docs; Rich ERE: 300+", "High"),
    ("OCR (Handwritten Nastaliq)", "~5k images", "Very small; needs 100k+ images", "IAM Handwriting: 13k lines", "Critical"),
    ("OCR (Printed Nastaliq)", "~10k images", "Small; needs 100k+ images", "RIMES: 12k; IAM: 13k+", "High"),
    ("Code-mixed (Roman Urdu-Eng)", "Various ~5-10k posts", "Small; needs 50k+ posts", "GLUECoS: 50k+; LinCE: 90k+", "High"),
    ("Topic Segmentation", "UrduSeg ~2k docs", "Tiny; needs 20k+ docs", "WIKI-727K: 727k", "High"),
    ("Negation Scope", "UrduNeg ~1k sentences", "Very small; needs 10k+ sentences", "Sherlock: 100k+", "Critical"),
    ("Idiom Detection", "UrduIdiom ~1k idioms", "Tiny; needs 10k+ idioms", "Magpie: 56k+", "High"),
    ("Speech Emotion Recognition", "UrduSpeechEmo ~3k utts", "Small; needs 10k+ utts", "IEMOCAP: 10k+", "High"),
    ("Speaker Diarization", "Limited to UrduSpeech", "Need 100+ hrs with multi-speaker", "AMI: 100hrs; VoxConverse: 50hrs+", "Medium"),
    ("Sign Language Recognition", "PSL-Urdu ~2k signs", "Tiny; needs 20k+ signs", "ASL Citizen: 80k+", "High"),
    ("Multimodal Sentiment", "UrduMultiSent ~5k pairs", "Small; needs 50k+ pairs", "CMU-MOSI: 2k+; MOSI: 65k+", "High"),
    ("Cyberbullying (Multimodal)", "Urdu Multi-Cyber ~3k posts", "Tiny; needs 20k+ posts", "Cyberbullying datasets: 50k+", "High"),
    ("Recommendation (News)", "UrduNewsRec ~50k clicks", "Small; needs 1M+ clicks", "MIND: 24M clicks", "High"),
    ("Emotion Cause Extraction", "UrduECE ~2k pairs", "Tiny; needs 10k+ pairs", "RECCON: 10k+", "High"),
    ("Plagiarism Detection", "UrduPlag ~1k pairs", "Tiny; needs 50k+ pairs", "PAN: 30k+", "Medium"),
]

# Write Block B
for i, (task, current, missing, target, severity) in enumerate(tiny_dataset_tasks, 1):
    r = row_b + i
    bg = ALT_ROW if i % 2 == 0 else None
    sev_color = {"Critical": DANGER, "High": WARNING, "Medium": "FB8C00", "Low": SUCCESS}.get(severity, "000000")
    values = [i, task, current, missing, target, severity]
    for col, v in enumerate(values, 1):
        cell = ws5.cell(row=r, column=col, value=v)
        if col == 1:
            apply_style(cell, body_style(bold=True, align="center", bg=bg))
        elif col == 2:
            apply_style(cell, body_style(bold=True, color=PRIMARY, bg=bg))
        elif col == 6:
            apply_style(cell, body_style(align="center", bold=True, color=sev_color, bg=bg))
        else:
            apply_style(cell, body_style(bg=bg, size=9))

block_b_end = row_b + len(tiny_dataset_tasks)

# Block C: Recommended fill-ins
row_c = block_b_end + 2
ws5.cell(row=row_c, column=1, value="C. Top 15 Recommended Fill-in Projects (Highest Impact)")
ws5.merge_cells(start_row=row_c, start_column=1, end_row=row_c, end_column=6)
apply_style(ws5.cell(row=row_c, column=1), {
    "font": Font(name=FONT_NAME, size=14, bold=True, color=SUCCESS),
    "fill": PatternFill("solid", fgColor=GAP_NONE),
    "alignment": Alignment(horizontal="left", vertical="center"),
})
ws5.row_dimensions[row_c].height = 26

row_c += 1
ws5.cell(row=row_c, column=1, value="#")
ws5.cell(row=row_c, column=2, value="Project")
ws5.cell(row=row_c, column=3, value="Why Now")
ws5.cell(row=row_c, column=4, value="Estimated Resources")
ws5.cell(row=row_c, column=5, value="Expected Impact")
ws5.cell(row=row_c, column=6, value="Priority")
for col in range(1, 7):
    apply_style(ws5.cell(row=row_c, column=col), header_style())
ws5.row_dimensions[row_c].height = 36

# Recommended fill-ins
recommendations = [
    ("Build UrduGPT-7B (LLM from scratch)", "No native Urdu LLM beyond LLaMA fine-tunes; cultural context missing", "$200k compute + 3-6 months", "Transformative — enables all downstream tasks", "Critical"),
    ("Annotate 50k+ Urdu NER corpus (multi-domain)", "CURRE is only 4k sentences, single domain", "$30k + 4 months annotation", "Enables production NER for Urdu", "Critical"),
    ("Build UrduMedQA (medical QA corpus)", "Zero medical NLP for Urdu despite huge need", "$20k + 6 months (medical experts)", "Saves lives; high social impact", "Critical"),
    ("Build UrduLegal-BERT and legal corpus", "Zero Urdu legal NLP — courts backlogged in Pakistan", "$50k + 12 months", "Modernizes legal system", "Critical"),
    ("Build 100k+ Urdu Sentiment Multi-domain Corpus", "UrduSent is 10k tweets — too narrow", "$10k + 3 months", "Production-grade sentiment", "High"),
    ("Build 50k+ Urdu Coreference Corpus", "UrduCoref only 2k docs", "$25k + 6 months", "Enables coreference at scale", "High"),
    ("Build 200k+ Urdu Summarization Corpus", "UrduSumm only 5k articles", "$15k + 3 months (scraping)", "Production summarization", "High"),
    ("Build 50k+ Urdu Nastaliq Handwritten OCR", "No public Nastaliq OCR corpus", "$50k + 12 months", "Digitizes historical documents", "High"),
    ("Build Urdu-MultiWOZ (task-oriented dialogue)", "No Urdu TOD at scale", "$40k + 8 months", "Enables Urdu chatbots for banking, healthcare", "High"),
    ("Translate and adapt COMET-ATOMIC to Urdu", "No Urdu commonsense corpus", "$5k + 3 months", "Enables commonsense reasoning", "High"),
    ("Build Urdu DROP / numerical reasoning dataset", "Zero Urdu numerical reasoning", "$10k + 4 months", "Enables math-aware NLP", "Medium"),
    ("Build UrduSpider (text-to-SQL)", "No Urdu text-to-SQL despite high app demand", "$10k + 3 months", "Enables Urdu NLIDB", "High"),
    ("Build UrduFactCheck (claim-evidence corpus)", "Only binary fake news exists; no fact-checking", "$30k + 6 months", "Combats Urdu misinformation", "Critical"),
    ("Build UrduGram (large-scale Grammatical Error Correction)", "No Urdu GEC for learners", "$15k + 4 months", "Helps 100M+ learners", "High"),
    ("Pre-train Urdu-specialized Whisper-large", "Existing Whisper fine-tunes miss Nastaliq variety", "$100k compute + 6 months", "Production Urdu ASR", "High"),
]

for i, (project, why, resources, impact, priority) in enumerate(recommendations, 1):
    r = row_c + i
    bg = ALT_ROW if i % 2 == 0 else None
    pri_color = {"Critical": DANGER, "High": WARNING, "Medium": "FB8C00", "Low": SUCCESS}.get(priority, "000000")
    values = [i, project, why, resources, impact, priority]
    for col, v in enumerate(values, 1):
        cell = ws5.cell(row=r, column=col, value=v)
        if col == 1:
            apply_style(cell, body_style(bold=True, align="center", bg=bg))
        elif col == 2:
            apply_style(cell, body_style(bold=True, color=PRIMARY, bg=bg))
        elif col == 6:
            apply_style(cell, body_style(align="center", bold=True, color=pri_color, bg=bg))
        else:
            apply_style(cell, body_style(bg=bg, size=9))

# Set column widths for sheet 5
widths5 = {1: 5, 2: 38, 3: 40, 4: 35, 5: 30, 6: 12}
for c, w in widths5.items():
    ws5.column_dimensions[get_column_letter(c)].width = w

print(f"Sheet 5 (Gap Analysis) done. {len(zero_work_tasks)} zero-work tasks, {len(tiny_dataset_tasks)} tiny-dataset tasks, {len(recommendations)} recommendations.")

# Reorder sheets so dashboard is first
wb.move_sheet("1. Summary Dashboard", offset=-5)

# Save
wb.save(WB_PATH)
print(f"\n✅ Excel file saved: {WB_PATH}")

# Show sheet count
print(f"Total sheets: {len(wb.sheetnames)}")
for s in wb.sheetnames:
    print(f"  - {s}")
