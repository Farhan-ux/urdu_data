# UrduNews-464: A Multi-Source Urdu News Dataset for Topic Modeling and Document Clustering

## Dataset Summary

UrduNews-464 is a curated dataset of 464 Urdu news articles scraped from four major Pakistani news outlets in September 2026. The dataset is designed for benchmarking topic modeling and document clustering methods on Urdu text.

## Sources

| Source | Articles | URL |
|--------|----------|-----|
| BBC Urdu | 106 | https://www.bbc.com/urdu |
| Express News | 150 | https://www.express.pk |
| Jang News | 127 | https://jang.com.pk |
| Nawa-i-Waqt | 81 | https://www.nawaiwaqt.com.pk |
| **Total** | **464** | |

## Section Distribution (auto-classified)

| Section | Articles |
|---------|----------|
| pakistan | 128 |
| world | 112 |
| crime | 62 |
| entertainment | 38 |
| sports | 36 |
| business | 28 |
| science | 26 |
| lifestyle | 18 |
| general | 16 |

## Dataset Statistics

- **Total articles**: 464
- **Total words**: 240,716
- **Average words per article**: 519
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
@misc{urdunews464,
  title={UrduNews-464: A Multi-Source Urdu News Dataset for Topic Modeling and Document Clustering},
  author={Anonymous},
  year={2026},
  note={Dataset available at [repository URL]}
}
```

## Ethics

All articles were scraped from publicly accessible news websites. The dataset is intended for research purposes only. Copyright of individual articles remains with the respective publishers.
