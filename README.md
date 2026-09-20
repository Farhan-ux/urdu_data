# Urdu NLP Research

A comprehensive research repository covering **Urdu Natural Language Processing** — including a systematic literature survey of 250+ papers, a curated dataset catalog, feasibility analysis of research gaps, and a working topic modeling benchmark on a newly-built Urdu news corpus.

## 📊 Repository Contents

### 1. Literature Survey (`download/Urdu_NLP_Research_Survey.xlsx`)

A 6-sheet Excel workbook cataloguing the Urdu NLP research landscape:

| Sheet | Contents |
|-------|----------|
| **1. Summary Dashboard** | Headline KPIs + papers-per-year chart + task distribution pie + dataset availability breakdown |
| **2. All Papers** | 250 Urdu NLP papers (2002–2026) with title, authors, year, venue, task, dataset, model, score, URL, public availability |
| **3. Task Coverage** | 118 NLP tasks × Urdu maturity (None/Small/Emerging/Mature) × gap level |
| **4. Dataset Catalog** | 119 datasets with size, public?, one-click download?, URL (HTTP-verified), license, gaps |
| **5. Gap Analysis** | 35 zero-work tasks + 43 tiny-dataset tasks + 15 recommended fill-in projects |
| **6. Feasibility & ROI** | 44 gap projects ranked by ROI score (effort × compute × labeling × publication potential) |

### 2. Topic Modeling Benchmark (`urdu_topic/`)

Working pipeline scraped from 4 Pakistani news outlets, with full preprocessing + topic modeling + clustering evaluation:

- **Dataset**: 464 articles, 240k words, 9 auto-classified sections
- **Sources**: BBC Urdu, Express, Jang, Nawa-i-Waqt
- **Models**: LDA, NMF, K-Means, SVD+KMeans, Spectral, Agglomerative, LDA+KMeans, TF-IDF+LDA+PCA
- **Best result**: TF-IDF+LDA PCA+KMeans (NMI=0.355, V-measure=0.355)

```
urdu_topic/
├── scripts/                    # All Python scripts (scrapers, models, figures)
│   ├── 01_scrape_bbc.py
│   ├── 02–07_scrape_*.py       # Multi-source scrapers
│   ├── 08_preprocess.py
│   ├── 09_train_models.py      # LDA, NMF, K-Means, SVD
│   ├── 10_train_round2.py      # Agglomerative, Spectral, ensemble
│   ├── 11_make_figures.py
│   ├── 12_package_dataset.py
│   └── urdu_preprocess.py      # Urdu tokenizer + stopwords + normalizer
├── data/                       # Scraped articles (JSON)
├── results/                    # Model outputs, evaluations, clusters
├── figures/                    # 8 publication-ready PNGs
├── dataset_release/            # Packaged dataset for release
│   ├── urdu_news_articles.jsonl
│   ├── urdu_news_articles.csv
│   ├── train.csv / test.csv
│   ├── vocabulary.txt
│   ├── dataset_stats.json
│   ├── urdu_preprocess.py
│   └── README.md
└── paper/                      # Paper draft (in progress)
```

### 3. Survey Compilation Scripts (`scripts/`)

The Python scripts used to build the literature survey Excel file:

- `papers_data.py` — Database of 250 Urdu NLP papers
- `build_excel.py` — Builds sheets 1–3
- `build_excel_part2.py` — Builds sheets 4–5
- `build_excel_sheet6.py` — Builds sheet 6 (Feasibility & ROI)
- `verify_urls.py` — HTTP-verifies all dataset URLs
- `parse_searches.py` — Parses web search results

## 🚀 Quick Start

### Run the topic modeling pipeline

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Scrape articles (or use the pre-scraped data in urdu_topic/data/)
cd urdu_topic/scripts
python 07_scrape_final.py

# 3. Preprocess
python 08_preprocess.py

# 4. Train models
python 09_train_models.py
python 10_train_round2.py

# 5. Generate figures
python 11_make_figures.py

# 6. Package dataset for release
python 12_package_dataset.py
```

### Use the dataset

```python
import pandas as pd
df = pd.read_csv("urdu_topic/dataset_release/urdu_news_articles.csv")
print(f"{len(df)} articles, {df['source'].nunique()} sources, {df['section'].nunique()} sections")
```

## 📈 Key Findings

### From the literature survey
- **250 Urdu NLP papers** catalogued across **63 NLP tasks**
- **119 unique datasets** identified; only ~75 are publicly downloadable
- **35 NLP tasks** have ZERO Urdu work (critical gaps)
- **43 tasks** have tiny datasets (<5k samples) vs English equivalents
- **Top 5 easy-win projects** (ROI 9/10): COMET-ATOMIC-Urdu, UrduSpider, DROP-Urdu, Urdu Topic Modeling at scale, Urdu Document Clustering

### From the topic modeling benchmark
| Method | NMI | ARI | V-measure |
|--------|-----|-----|-----------|
| TF-IDF+LDA+PCA+KMeans | 0.355 | 0.143 | 0.355 |
| NMF (k=9) | 0.354 | 0.175 | 0.354 |
| LDA-features+KMeans | 0.354 | 0.192 | 0.354 |
| LDA (k=10) | 0.340 | 0.199 | 0.340 |
| K-Means (k=9) | 0.325 | 0.156 | 0.325 |
| Spectral (k=10) | 0.320 | 0.140 | 0.320 |
| Majority baseline | 0.000 | 0.000 | 0.000 |

## 📋 License

- **Code**: MIT
- **Dataset**: CC BY 4.0
- **Survey Excel**: CC BY 4.0

## 📜 Citation

```bibtex
@misc{urdu_nlp_research_2026,
  title={Urdu NLP Research: Survey, Dataset, and Topic Modeling Benchmark},
  author={Farhan Ch},
  year={2026},
  url={https://github.com/Farhan-ux/urdu-nlp-research}
}
```

## ⚠️ Ethics

All articles were scraped from publicly accessible news websites. Copyright of individual articles remains with the respective publishers. The dataset is intended for research purposes only.
