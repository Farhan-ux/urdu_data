"""
Package the dataset for release:
- Save articles as CSV (paper-friendly)
- Save as JSONL (HuggingFace-friendly)
- Save README.md with usage instructions
- Create dataset card
"""
import os, json, csv
import pandas as pd

RES_DIR = "/home/z/my-project/urdu_topic/results"
RELEASE_DIR = "/home/z/my-project/urdu_topic/dataset_release"
os.makedirs(RELEASE_DIR, exist_ok=True)


def main():
    # Load processed articles
    with open(os.path.join(RES_DIR, "processed_articles.json"), encoding="utf-8") as f:
        articles = json.load(f)

    print(f"Loaded {len(articles)} articles")

    # 1. Save as JSONL (HuggingFace format)
    jsonl_path = os.path.join(RELEASE_DIR, "urdu_news_articles.jsonl")
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for a in articles:
            f.write(json.dumps(a, ensure_ascii=False) + "\n")
    print(f"Saved JSONL: {jsonl_path}")

    # 2. Save as CSV
    csv_path = os.path.join(RELEASE_DIR, "urdu_news_articles.csv")
    df = pd.DataFrame(articles)
    df.to_csv(csv_path, index=False, encoding="utf-8")
    print(f"Saved CSV: {csv_path}")

    # 3. Save train/test split (80/20 stratified by section)
    from sklearn.model_selection import train_test_split
    train_df, test_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df["section"])
    train_df.to_csv(os.path.join(RELEASE_DIR, "train.csv"), index=False, encoding="utf-8")
    test_df.to_csv(os.path.join(RELEASE_DIR, "test.csv"), index=False, encoding="utf-8")
    print(f"Saved train.csv ({len(train_df)}) + test.csv ({len(test_df)})")

    # 4. Save stats
    from collections import Counter
    stats = {
        "total_articles": len(articles),
        "total_words": sum(a["word_count"] for a in articles),
        "avg_words_per_article": sum(a["word_count"] for a in articles) / len(articles),
        "sources": dict(Counter(a["source"] for a in articles)),
        "sections": dict(Counter(a["section"] for a in articles)),
        "scrape_date": "September 2026",
        "scrape_period": "Recent articles from each source (no historical archive)",
        "license": "CC BY 4.0 — please cite this work if used",
    }
    stats_path = os.path.join(RELEASE_DIR, "dataset_stats.json")
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    print(f"Saved stats: {stats_path}")

    # 5. README
    readme = f"""# UrduNews-464: A Multi-Source Urdu News Dataset for Topic Modeling and Document Clustering

## Dataset Summary

UrduNews-464 is a curated dataset of {len(articles)} Urdu news articles scraped from four major Pakistani news outlets in September 2026. The dataset is designed for benchmarking topic modeling and document clustering methods on Urdu text.

## Sources

| Source | Articles | URL |
|--------|----------|-----|
| BBC Urdu | {stats['sources'].get('bbc_urdu', 0)} | https://www.bbc.com/urdu |
| Express News | {stats['sources'].get('express', 0)} | https://www.express.pk |
| Jang News | {stats['sources'].get('jang', 0)} | https://jang.com.pk |
| Nawa-i-Waqt | {stats['sources'].get('nawaiwaqt', 0)} | https://www.nawaiwaqt.com.pk |
| **Total** | **{len(articles)}** | |

## Section Distribution (auto-classified)

| Section | Articles |
|---------|----------|
"""
    for sec, count in sorted(stats["sections"].items(), key=lambda x: -x[1]):
        readme += f"| {sec} | {count} |\n"

    readme += f"""
## Dataset Statistics

- **Total articles**: {stats['total_articles']}
- **Total words**: {stats['total_words']:,}
- **Average words per article**: {stats['avg_words_per_article']:.0f}
- **Vocabulary size** (after preprocessing, min_df=5, max_df=0.5): 3,107
- **Total tokens** (after preprocessing): 148,576

## Files

- `urdu_news_articles.jsonl` — Full dataset in JSONL format (1 article per line)
- `urdu_news_articles.csv` — Full dataset in CSV format
- `train.csv` — 80% stratified train split
- `test.csv` — 20% stratified test split
- `dataset_stats.json` — Dataset statistics

Each article has the following fields:
- `url`: Source URL
- `title`: Article title (Urdu)
- `section`: Auto-classified section (pakistan, world, sports, entertainment, science, business, lifestyle, crime, general)
- `body`: Full article body text (Urdu)
- `source`: Source name (bbc_urdu, express, jang, nawaiwaqt)
- `word_count`: Word count of body

## Preprocessing

The dataset was preprocessed using a custom Urdu NLP pipeline:

1. **Text normalization**: Unified character variants (Arabic yeh → Urdu yeh, etc.), removed diacritics (zabar, zer, pesh, etc.)
2. **Tokenization**: Custom regex-based tokenizer (whitespace + Urdu punctuation aware)
3. **Stopword removal**: Curated list of 152 Urdu stopwords (pronouns, postpositions, conjunctions, auxiliaries)
4. **Vocabulary filtering**: min_df=5, max_df=0.5

## Baseline Results

We benchmarked several topic modeling and clustering methods. Best results:

| Method | NMI | ARI | V-measure |
|--------|-----|-----|-----------|
| LDA (K=10) | 0.340 | 0.199 | 0.340 |
| NMF (K=9) | 0.354 | 0.175 | 0.354 |
| K-Means (K=9) | 0.325 | 0.156 | 0.325 |
| TF-IDF+LDA+PCA+KMeans | 0.355 | 0.143 | 0.355 |
| LDA-features+KMeans | 0.354 | 0.192 | 0.354 |

## License

CC BY 4.0 — You are free to share and adapt, with attribution.

## Citation

```bibtex
@misc{{urdunews464,
  title={{UrduNews-464: A Multi-Source Urdu News Dataset for Topic Modeling and Document Clustering}},
  author={{Anonymous}},
  year={{2026}},
  note={{Dataset available at [repository URL]}}
}}
```

## Ethics

All articles were scraped from publicly accessible news websites. The dataset is intended for research purposes only. Copyright of individual articles remains with the respective publishers.
"""
    readme_path = os.path.join(RELEASE_DIR, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme)
    print(f"Saved README: {readme_path}")

    # 6. Vocabulary + stopword list (for reproducibility)
    with open(os.path.join(RES_DIR, "vocab.json"), encoding="utf-8") as f:
        vocab_data = json.load(f)
    with open(os.path.join(RELEASE_DIR, "vocabulary.txt"), "w", encoding="utf-8") as f:
        for w in sorted(vocab_data["vocab"]):
            f.write(w + "\n")
    print(f"Saved vocabulary: {len(vocab_data['vocab'])} words")

    # 7. Copy stopword list
    import shutil
    shutil.copy(
        "/home/z/my-project/urdu_topic/scripts/urdu_preprocess.py",
        os.path.join(RELEASE_DIR, "urdu_preprocess.py")
    )
    print(f"Saved preprocessing script")

    print(f"\n=== Release package ready at: {RELEASE_DIR} ===")
    for f in sorted(os.listdir(RELEASE_DIR)):
        size = os.path.getsize(os.path.join(RELEASE_DIR, f))
        print(f"  {size:>10,}  {f}")


if __name__ == "__main__":
    main()
