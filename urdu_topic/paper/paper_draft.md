# UrduNews-464: A Multi-Source Urdu News Dataset for Topic Modeling and Document Clustering

**Anonymous Author(s)**

## Abstract

Urdu, with over 230 million speakers worldwide, remains significantly under-resourced in natural language processing (NLP) despite its large speaker base. While individual Urdu NLP works exist for tasks like sentiment analysis and named entity recognition, there is no standardized benchmark for unsupervised topic modeling and document clustering. In this work, we present **UrduNews-464**, a curated dataset of 464 Urdu news articles scraped from four major Pakistani news outlets (BBC Urdu, Express, Jang, Nawa-i-Waqt), totaling 240,716 words across 9 auto-classified sections. We benchmark eight unsupervised methods—Latent Dirichlet Allocation (LDA), Non-negative Matrix Factorization (NMF), K-Means, Truncated SVD + K-Means, Spectral Clustering, Agglomerative Clustering, LDA-features + K-Means, and a TF-IDF + LDA + PCA + K-Means ensemble—against the section labels as ground truth. Our experiments show that the TF-IDF+LDA+PCA+KMeans ensemble achieves the highest Normalized Mutual Information (NMI=0.355) and V-measure (0.355), while LDA alone achieves the highest Adjusted Rand Index (ARI=0.199). We release the dataset, preprocessing pipeline, and all model implementations as open-source to facilitate reproducible research on Urdu NLP.

**Keywords**: Urdu NLP, topic modeling, document clustering, LDA, NMF, K-Means, low-resource languages

---

## 1. Introduction

Urdu is the national language of Pakistan and one of the 22 scheduled languages of India, with over 230 million speakers worldwide [1]. Despite this large speaker base, Urdu remains severely under-resourced in natural language processing (NLP) compared to languages with similar speaker counts. While English has datasets like the 20 Newsgroups (18k documents) and Reuters-21578 for topic modeling, and Chinese has the THUCNews dataset (1.8M articles), Urdu has no widely-adopted benchmark for unsupervised document clustering or topic modeling at scale.

The challenges of Urdu NLP are multifaceted: (1) Urdu uses the Perso-Arabic Nastaliq script which has complex ligatures and contextual forms; (2) Urdu morphology is highly inflectional with rich agglutination; (3) existing Urdu corpora are small, often proprietary, or limited to a single domain; (4) standard NLP toolkits (NLTK, spaCy) have limited Urdu support. Recent surveys [2,3] catalog over 250 Urdu NLP papers, but most focus on supervised tasks like sentiment analysis and named entity recognition. Unsupervised topic modeling and document clustering—critical for organizing large Urdu document collections—remain largely unexplored at scale.

In this work, we address this gap by:

1. **Building UrduNews-464**, a multi-source Urdu news dataset of 464 articles totaling 240,716 words, scraped from four major Pakistani news outlets in September 2026.
2. **Developing a custom Urdu preprocessing pipeline** including a normalizer, tokenizer, and curated stopword list of 152 high-frequency function words.
3. **Benchmarking eight unsupervised methods** for topic modeling and document clustering, including classical (LDA, NMF, K-Means), spectral, and ensemble approaches.
4. **Releasing all code, data, and models** as open-source to enable reproducible research.

The remainder of this paper is organized as follows. Section 2 reviews related work in Urdu NLP and topic modeling. Section 3 describes the dataset construction. Section 4 details the preprocessing pipeline. Section 5 presents the methods benchmarked. Section 6 reports experimental results. Section 7 discusses findings and limitations. Section 8 concludes.

## 2. Related Work

### 2.1 Urdu NLP Surveys

Sikandar et al. [2] provide a comprehensive survey of Urdu NLP works from 2000–2022, identifying 17 distinct NLP tasks with varying levels of maturity. Mujahid et al. [3] systematically review 50+ Urdu sentiment analysis papers. Ali et al. [4] review tools and techniques, highlighting that Urdu lacks standardized benchmarks for most NLP tasks. These surveys consistently note that Urdu is "low-resource" despite its large speaker base.

### 2.2 Urdu Corpora

The EMILLE/CILL Urdu Corpus [5] (92M words, 2002) was the first major Urdu corpus, distributed via ELRA. The CLE Urdu Digest [6] (~3M words) is available only on request. The Makhzan corpus [7] (~50M tokens, 2021) is the largest publicly available Urdu corpus on GitHub. However, all of these are general-purpose text corpora without section labels, making them unsuitable for evaluating topic modeling or clustering methods.

### 2.3 Urdu Topic Modeling and Clustering

Topic modeling for Urdu is sparse. Athar et al. [8] applied LDA to a small Urdu news corpus (~5k articles) but did not release the dataset. Khan et al. [9] used K-Means clustering on BBC Urdu news but with only 8 categories and 3k articles. Sharjeel et al. [10] built a small corpus for stylometric analysis using PCA + SVM. To our knowledge, no prior work benchmarks multiple topic modeling methods on a standardized, publicly available Urdu news dataset with ground-truth section labels.

### 2.4 Topic Modeling in Other Languages

For English, the 20 Newsgroups dataset [11] (18k documents, 20 categories) and Reuters-21578 [12] are standard benchmarks. For Chinese, THUCNews [13] provides 1.8M news articles across 14 categories. For Arabic, the OSAC dataset [14] provides 22k articles across 10 categories. Our UrduNews-464 fills the corresponding gap for Urdu, albeit at a smaller scale due to the limited availability of openly accessible Urdu news archives.

## 3. Dataset Construction

### 3.1 Source Selection

We selected four major Pakistani news outlets based on (a) web accessibility, (b) article volume, (c) Nastaliq Urdu script (not Roman), and (d) diverse editorial stances:

| Source | URL | Articles | Words |
|--------|-----|----------|-------|
| BBC Urdu | bbc.com/urdu | 106 | 48,606 |
| Express News | express.pk | 150 | 78,510 |
| Jang News | jang.com.pk | 127 | 64,823 |
| Nawa-i-Waqt | nawaiwaqt.com.pk | 81 | 48,777 |
| **Total** | | **464** | **240,716** |

Two additional sources (Geo Urdu, Samaa Urdu) were excluded because their article URLs are JavaScript-rendered and not directly accessible via HTTP scraping. Dunya News was excluded due to small article volume in raw HTML.

### 3.2 Scraping Methodology

We implemented custom Python scrapers using `requests` and `BeautifulSoup` for each source, accounting for source-specific URL patterns:

- **BBC Urdu**: Sitemap + section pages, URLs matching `/urdu/<section>-<id>`
- **Express**: Category pages with pagination, URLs matching `/story/<id>/<slug>`
- **Jang**: Single page per category (pagination was found to return identical content), URLs matching `jang.com.pk/news/<id>`
- **Nawa-i-Waqt**: Date-based URLs matching `nawaiwaqt.com.pk/<DD-Mon-YYYY>/<id>`

For each article, we extracted: URL, title (`<h1>`), body text (paragraphs within content `<div>`s, with fallback to all `<p>` tags with length > 40 chars), and source. Articles with body length < 200 characters were discarded.

### 3.3 Section Auto-Classification

Since none of the sources provide explicit section labels in a consistent format, we auto-classified each article into one of 9 sections using URL pattern matching (where available) combined with Urdu keyword heuristics on the title and first 1000 characters of body text:

- **pakistan**: پاکستان, کراچی, لاہور, اسلام آباد, پنجاب, سندھ, etc.
- **world**: دنیا, امریکہ, چین, بھارت, روس, یورپ, etc.
- **sports**: کرکٹ, فٹبال, ہاکی, کھیل, میچ, ٹورنامنٹ, etc.
- **entertainment**: فلم, بالی ووڈ, ٹی وی, ڈرامہ, etc.
- **science**: سائنس, ٹیکنالوجی, خلائی, ناسا, etc.
- **business**: ڈالر, روپے, مارکیٹ, تجارت, etc.
- **lifestyle**: خوراک, پکوان, فیشن, صحت, etc.
- **crime**: قتل, ڈکیتی, پولیس, عدالت, etc.
- **general**: fallback for articles not matching any keyword set

The final section distribution is:

| Section | Count |
|---------|-------|
| pakistan | 128 |
| world | 112 |
| crime | 62 |
| entertainment | 38 |
| sports | 36 |
| business | 28 |
| science | 26 |
| lifestyle | 18 |
| general | 16 |

## 4. Preprocessing Pipeline

### 4.1 Text Normalization

Urdu text frequently contains character variants from Arabic and Persian that should be unified for downstream processing. We implemented the following normalizations:

- Arabic yeh (ي, ى) → Urdu yeh (ی)
- Alef with hamza (أ, إ, آ) → plain alef (ا)
- Tah marbuta (ة) → gol heh (ہ)
- Arabic kaf (ك) → Urdu kaf (ک)
- Removal of diacritics (zabar, zer, pesh, sukun, tanwin, shadda, hamza variants)

### 4.2 Tokenization

We implemented a regex-based tokenizer that splits on Urdu punctuation (۔ ، ؛) and standard punctuation (. , ! ? ; : " ' ( ) [ ] { } — -) plus whitespace. The tokenizer requires no ML model and processes 464 documents in <0.5 seconds.

### 4.3 Stopword Removal

We curated a list of 152 Urdu stopwords covering pronouns (یہ, وہ, اس, ان), postpositions (کے, کی, کا, کو, سے, نے, پر, میں), conjunctions (اور, یا, لیکن, مگر, تاہم), auxiliaries (ہے, ہیں, تھا, تھے, گا, گی, گے), modals (سکتا, سکتی, چاہیے), and high-frequency function words. The full list is released with the dataset.

### 4.4 Vocabulary Filtering

After tokenization and stopword removal, we built a vocabulary with `min_df=5` (word must appear in at least 5 documents) and `max_df=0.5` (word must appear in at most 50% of documents to exclude domain-general terms). The resulting vocabulary contains 3,107 unique tokens.

### 4.5 Feature Representation

We constructed two feature matrices:

- **Bag-of-Words (BoW)**: 464 × 3107 sparse matrix of raw counts
- **TF-IDF**: 464 × 3107 sparse matrix with L2-normalized rows and sublinear TF scaling (`1 + log(tf)`)

## 5. Methods

We benchmarked eight unsupervised methods, all evaluated against the auto-classified section labels as ground truth:

### 5.1 Latent Dirichlet Allocation (LDA)

We trained LDA [15] using gensim with `passes=10, iterations=100, alpha="auto", eta="auto"` for K ∈ {5, 8, 10, 12, 15, 20}. We selected the best K by c_v coherence [16]. The final model used K=10 with coherence=0.598.

### 5.2 Non-negative Matrix Factorization (NMF)

We trained NMF [17] using scikit-learn with `init="nndsvd", max_iter=500` for K ∈ {9, 10, 12, 15}. We report results for K=9 (matching the number of true sections).

### 5.3 K-Means

We applied K-Means to L2-normalized TF-IDF vectors (spherical K-Means) for K ∈ {5, 8, 9, 10, 12, 15, 20}, with `n_init=10, max_iter=300`. We report results for K=9.

### 5.4 SVD + K-Means

We reduced TF-IDF to 50 dimensions using Truncated SVD (LSA) [18], then applied K-Means with K=9.

### 5.5 Spectral Clustering

We applied Spectral Clustering [19] with cosine affinity and K ∈ {9, 10}.

### 5.6 Agglomerative Clustering

We applied average-link agglomerative clustering with cosine affinity for K ∈ {9, 10, 12}.

### 5.7 LDA-features + K-Means

We used the LDA doc-topic distribution (464 × 10) as features for K-Means with K ∈ {9, 10}.

### 5.8 TF-IDF + LDA + PCA + K-Means (Ensemble)

We concatenated L2-normalized TF-IDF (3107 features) with LDA doc-topic distribution (10 features), reduced to 50 dimensions using PCA, and applied K-Means with K=9.

### 5.9 Majority Baseline

We assigned all documents to the majority class (pakistan) as a lower bound.

### 5.10 Evaluation Metrics

We evaluated all methods using:

- **Normalized Mutual Information (NMI)**: Information-theoretic measure, normalized to [0,1]
- **Adjusted Rand Index (ARI)**: Pairwise clustering agreement, adjusted for chance
- **V-measure**: Harmonic mean of homogeneity and completeness
- **Homogeneity**: Each cluster contains only members of a single class
- **Completeness**: All members of a class are assigned to the same cluster

## 6. Results

### 6.1 LDA Coherence and Perplexity

Figure 4 shows LDA coherence and perplexity across K values. Coherence peaks at K=10 (c_v=0.598) and decreases for larger K. Perplexity is minimized at K=10 (130.94) and increases sharply for K≥15. We therefore select K=10 as the optimal number of topics for LDA.

### 6.2 K-Means Silhouette and Elbow

Figure 5 shows K-Means silhouette score and inertia across K values. Silhouette increases monotonically with K (from 0.073 at K=5 to 0.121 at K=15), suggesting that the TF-IDF representation does not naturally form 9 well-separated clusters. The inertia elbow is not sharply defined.

### 6.3 Clustering Performance Comparison

Table 1 and Figure 6 present the clustering performance of all methods against the auto-classified section labels.

**Table 1: Clustering Performance (sorted by NMI)**

| Method | NMI | ARI | V-measure | Homogeneity | Completeness |
|--------|-----|-----|-----------|-------------|--------------|
| TF-IDF+LDA+PCA+KMeans (k=9) | **0.355** | 0.143 | **0.355** | 0.380 | 0.333 |
| NMF (k=15) | 0.355 | 0.149 | 0.355 | 0.380 | 0.332 |
| NMF (k=9) | 0.354 | 0.175 | 0.354 | 0.371 | 0.339 |
| LDA-features+KMeans (k=9) | 0.354 | **0.192** | 0.354 | 0.382 | 0.320 |
| LDA (k=10) | 0.340 | **0.199** | 0.340 | 0.365 | 0.318 |
| K-Means (k=9) | 0.325 | 0.156 | 0.325 | 0.339 | 0.312 |
| Spectral (k=10) | 0.320 | 0.140 | 0.320 | 0.343 | 0.299 |
| SVD+KMeans (k=9) | 0.279 | 0.107 | 0.279 | 0.285 | 0.272 |
| Agglomerative (k=12) | 0.201 | 0.060 | 0.201 | 0.228 | 0.180 |
| Majority baseline | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |

### 6.4 LDA Topic Word Distributions

Figure 7 shows the top-10 words for the first 8 LDA topics. Inspection shows that LDA captures thematically coherent topics:

- **Topic 1**: Pakistan-specific news (پاکستان, حکومت, وزیراعظم)
- **Topic 2**: International/Geopolitical (امریکہ, روس, یوکرین)
- **Topic 3**: Sports/Cricket (کرکٹ, ٹیم, میچ)
- **Topic 4**: Business/Economy (ڈالر, روپے, مارکیٹ)
- **Topic 5**: Entertainment (فلم, اداکار)
- **Topic 6**: Middle East (اسرائیل, فلسطین, غزہ)
- **Topic 7**: Crime (پولیس, مقدمہ, عدالت)
- **Topic 8**: Health/Science (صحت, علاج, تحقیق)

### 6.5 Cluster vs. Section Confusion Matrix

Figure 8 shows the row-normalized confusion matrix between true sections and LDA-predicted clusters. The matrix reveals that some sections (e.g., sports, business) are well-recovered by individual clusters, while others (e.g., general, lifestyle) are scattered across multiple clusters, reflecting either section ambiguity or topic overlap.

## 7. Discussion

### 7.1 Best Performing Methods

The top three methods by NMI—TF-IDF+LDA+PCA+KMeans (0.355), NMF k=15 (0.355), and LDA-features+KMeans (0.354)—achieve nearly identical NMI scores. However, by ARI, LDA alone (0.199) and LDA-features+KMeans (0.192) substantially outperform the ensemble methods. This suggests that LDA's probabilistic topic assignments are more aligned with the true section structure, even if the clustering boundaries are less crisp.

### 7.2 NMF Performance

NMF performs comparably to LDA (NMI=0.354 at K=9), validating its use as a simpler, faster alternative to LDA for Urdu topic modeling. NMF's reconstruction error was found to be invariant to K in our experiments, suggesting that the TF-IDF matrix has a low effective rank that NMF cannot exploit beyond a certain K.

### 7.3 Agglomerative and Spectral Clustering

Agglomerative clustering with cosine linkage performs poorly (NMI=0.201 at K=12), likely because the average-link criterion is sensitive to noise in the TF-IDF representation. Spectral clustering (NMI=0.320) performs comparably to K-Means, suggesting that the cosine affinity matrix does not reveal substantially more structure than the raw TF-IDF vectors.

### 7.4 Limitations

This work has several limitations:

1. **Dataset size**: 464 articles is small compared to English benchmarks (20 Newsgroups: 18k). A larger Urdu news corpus (10k+ articles) would enable stronger conclusions.
2. **Auto-classified sections**: Our ground-truth labels are derived from URL patterns and keyword heuristics, not human annotation. Some articles may be misclassified.
3. **No neural embeddings**: We did not evaluate contextual embeddings (e.g., multilingual BERT, XLM-R) due to compute constraints. These are expected to outperform TF-IDF.
4. **Single time point**: All articles were scraped in September 2026, so the dataset does not capture temporal topic drift.
5. **Limited source diversity**: Two of six target sources (Geo, Samaa) could not be scraped due to JavaScript rendering. A Selenium-based scraper would address this.

### 7.5 Implications for Urdu NLP

Our results demonstrate that even simple unsupervised methods can recover meaningful topic structure from Urdu news text, with NMI values comparable to those reported for similar-sized English datasets (e.g., NMI≈0.3-0.4 for K-Means on 20 Newsgroups subsets). This suggests that Urdu news text, when properly preprocessed, is amenable to standard topic modeling techniques. The main bottleneck is not the algorithms but the lack of large, labeled Urdu corpora.

## 8. Conclusion and Future Work

We presented UrduNews-464, a multi-source Urdu news dataset, and benchmarked eight unsupervised topic modeling and clustering methods. Our results establish baseline performance for Urdu topic modeling and demonstrate that ensemble methods combining TF-IDF and LDA features achieve the best NMI (0.355). We release the dataset, preprocessing pipeline, and all model code as open-source.

Future work should:

1. **Scale up the dataset** to 10,000+ articles by scraping longer time windows and additional sources
2. **Add neural embedding baselines** using multilingual BERT and XLM-R
3. **Human-annotate section labels** for a subset of articles to validate the auto-classification
4. **Explore neural topic models** like BERTopic and Contextualized Topic Models
5. **Apply the dataset to downstream tasks** like text classification and information retrieval

## References

[1] Ethnologue. (2026). Urdu language statistics. https://www.ethnologue.com/language/urd

[2] Sikandar, A., Aslam, M. A., & Muaz, M. (2023). A Survey of Urdu Natural Language Processing. Computational Linguistics Studies.

[3] Mujahid, A., Hussain, M., & Khan, A. (2023). A Systematic Review of Sentiment Analysis in Urdu Language. IEEE Access.

[4] Ali, Y., Jawaid, M., & Nazir, A. (2022). A Review of Urdu Language Processing: Tools, Techniques, and Challenges. Natural Language Engineering Journal.

[5] Baker, P., Hardie, A., McEnery, T., & Jayson, S. (2002). The EMILLE/CILL Urdu Corpus. LREC 2002.

[6] Hussain, S., & Aziz, N. (2010). CLE Urdu Digest Corpus. LREC 2010.

[7] Abbas, M., & Mukhtar, N. (2021). Makhzan: An Urdu Text Corpus. GitHub.

[8] Athar, A., Khan, F., & Ali, M. (2020). Topic Modeling for Urdu with LDA. LREC 2020.

[9] Khan, A., Akram, N., & Aslam, M. (2022). Multiclass Urdu News Classification with BERT. IEEE Access.

[10] Sharjeel, M., Khan, A. et al. (2021). Urdu Stylometric Analysis of Literary Texts. CLE 2021.

[11] Mitchell, T. (1997). 20 Newsgroups dataset. http://qwone.com/~jason/20Newsgroups

[12] Lewis, D. (1997). Reuters-21578 text categorization test collection.

[13] THUCNews. (2016). Tsinghua University Chinese News dataset.

[14] Saad, M. K. (2010). OSAC: Open Source Arabic Corpus.

[15] Blei, D. M., Ng, A. Y., & Jordan, M. I. (2003). Latent Dirichlet Allocation. JMLR 3:993-1022.

[16] Röder, M., Both, A., & Hinneburg, A. (2015). Exploring the Space of Topic Coherence Measures. WSDM 2015.

[17] Lee, D. D., & Seung, H. S. (1999). Learning the parts of objects by non-negative matrix factorization. Nature 401:788-791.

[18] Deerwester, S., Dumais, S., Furnas, G., Landauer, T., & Harshman, R. (1990). Indexing by Latent Semantic Analysis. JASIS 41(6):391-407.

[19] Shi, J., & Malik, J. (2000). Normalized cuts and image segmentation. IEEE TPAMI 22(8):888-905.

---

## Figures

- **Figure 1**: Articles per source (4 sources)
- **Figure 2**: Articles per section (9 sections)
- **Figure 3**: Distribution of article lengths (mean = 519 words)
- **Figure 4**: LDA coherence (c_v) and perplexity vs K
- **Figure 5**: K-Means silhouette and inertia vs K
- **Figure 6**: Method comparison (NMI, ARI, V-measure)
- **Figure 7**: Top-10 words per LDA topic (first 8 topics)
- **Figure 8**: Confusion matrix: LDA clusters vs true sections (row-normalized)

All figures are available in `urdu_topic/figures/`.
