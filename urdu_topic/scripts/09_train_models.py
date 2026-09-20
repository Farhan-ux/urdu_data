"""
Train topic models:
- LDA (Latent Dirichlet Allocation) — multiple K values, pick best by coherence
- NMF (Non-negative Matrix Factorization)
- K-Means clustering (with TF-IDF + with embeddings)
- Evaluate: coherence (c_v), NMI, ARI, V-measure, homogeneity vs section labels
"""
import os, sys, json, time, warnings
import numpy as np
import scipy.sparse as sp
from collections import Counter, defaultdict

warnings.filterwarnings("ignore")

from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation, NMF, TruncatedSVD
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.metrics import (
    normalized_mutual_info_score, adjusted_rand_score,
    v_measure_score, homogeneity_score, completeness_score,
    silhouette_score
)
from sklearn.metrics.pairwise import cosine_similarity

import gensim
from gensim.models import LdaModel, CoherenceModel
from gensim.corpora import Dictionary

DATA_DIR = "/home/z/my-project/urdu_topic/data"
RES_DIR = "/home/z/my-project/urdu_topic/results"
os.makedirs(RES_DIR, exist_ok=True)


def load_data():
    with open(os.path.join(RES_DIR, "processed_articles.json")) as f:
        articles = json.load(f)
    with open(os.path.join(RES_DIR, "docs_tokens.json")) as f:
        docs_tokens = json.load(f)
    bow = sp.load_npz(os.path.join(RES_DIR, "bow.npz"))
    tfidf = sp.load_npz(os.path.join(RES_DIR, "tfidf.npz"))
    with open(os.path.join(RES_DIR, "vocab.json")) as f:
        vocab_data = json.load(f)
    return articles, docs_tokens, bow, tfidf, vocab_data


def get_section_labels(articles):
    return np.array([a["section"] for a in articles])


# ============================================================
# LDA via gensim (with coherence)
# ============================================================
def train_lda_gensim(docs_tokens, k_values=[5, 8, 10, 12, 15, 20]):
    """Train LDA for multiple K, evaluate by c_v coherence."""
    print(f"\n=== LDA Training (gensim) ===", flush=True)
    # Build gensim dict + corpus
    dictionary = Dictionary(docs_tokens)
    dictionary.filter_extremes(no_below=5, no_above=0.5)
    corpus = [dictionary.doc2bow(doc) for doc in docs_tokens]
    print(f"  Dict size: {len(dictionary)}", flush=True)
    print(f"  Corpus: {len(corpus)} docs", flush=True)

    results = []
    for k in k_values:
        t0 = time.time()
        print(f"  Training LDA k={k}...", flush=True, end=" ")
        lda = LdaModel(
            corpus=corpus,
            id2word=dictionary,
            num_topics=k,
            random_state=42,
            passes=10,
            iterations=100,
            alpha="auto",
            eta="auto",
            eval_every=None,
            chunksize=100,
        )
        # Coherence
        cm = CoherenceModel(model=lda, texts=docs_tokens, dictionary=dictionary, coherence="c_v")
        coherence = cm.get_coherence()
        # Perplexity (held-out, using bound on corpus)
        perplexity = np.exp2(-lda.log_perplexity(corpus))
        elapsed = time.time() - t0
        print(f"coherence={coherence:.4f} perplexity={perplexity:.2f} elapsed={elapsed:.1f}s", flush=True)

        # Top 10 words per topic
        topics_words = []
        for i in range(k):
            top = lda.show_topic(i, topn=10)
            topics_words.append([w for w, _ in top])

        results.append({
            "k": k,
            "coherence": float(coherence),
            "perplexity": float(perplexity),
            "elapsed_sec": float(elapsed),
            "topics": topics_words,
        })

    # Pick best K
    best = max(results, key=lambda r: r["coherence"])
    print(f"\n  Best K={best['k']} (coherence={best['coherence']:.4f})", flush=True)

    # Save
    with open(os.path.join(RES_DIR, "lda_results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"  Saved: lda_results.json", flush=True)

    # Train final LDA with best K and get doc-topic distribution
    best_k = best["k"]
    print(f"  Training final LDA with k={best_k}...", flush=True)
    final_lda = LdaModel(
        corpus=corpus, id2word=dictionary, num_topics=best_k,
        random_state=42, passes=20, iterations=200,
        alpha="auto", eta="auto", eval_every=None, chunksize=100,
    )
    # Doc-topic distribution
    doc_topics = np.zeros((len(corpus), best_k))
    for i, bow in enumerate(corpus):
        dist = final_lda.get_document_topics(bow, minimum_probability=0.0)
        for tid, prob in dist:
            doc_topics[i, tid] = prob
    np.save(os.path.join(RES_DIR, "lda_doc_topics.npy"), doc_topics)
    print(f"  Saved doc-topic matrix: shape={doc_topics.shape}", flush=True)

    # Predicted cluster = argmax
    lda_clusters = doc_topics.argmax(axis=1)
    np.save(os.path.join(RES_DIR, "lda_clusters.npy"), lda_clusters)

    return best, lda_clusters


# ============================================================
# NMF
# ============================================================
def train_nmf(tfidf, k_values=[5, 8, 10, 12, 15, 20]):
    print(f"\n=== NMF Training ===", flush=True)
    results = []
    for k in k_values:
        t0 = time.time()
        print(f"  Training NMF k={k}...", flush=True, end=" ")
        nmf = NMF(n_components=k, random_state=42, max_iter=500, l1_ratio=0.5, alpha_W=0.1)
        W = nmf.fit_transform(tfidf)
        H = nmf.components_
        recon_err = nmf.reconstruction_err_
        elapsed = time.time() - t0
        print(f"recon_err={recon_err:.2f} elapsed={elapsed:.1f}s", flush=True)

        # Top 10 words per topic
        vocab = json.load(open(os.path.join(RES_DIR, "vocab.json")))["vocab"]
        topics_words = []
        for i in range(k):
            top_idx = H[i].argsort()[::-1][:10]
            topics_words.append([vocab[j] for j in top_idx])

        results.append({
            "k": k,
            "reconstruction_err": float(recon_err),
            "elapsed_sec": float(elapsed),
            "topics": topics_words,
        })

    # For NMF, pick k=10 (since we have 9 sections)
    best_k = 10
    print(f"\n  Using k={best_k} for evaluation", flush=True)
    nmf = NMF(n_components=best_k, random_state=42, max_iter=500, l1_ratio=0.5, alpha_W=0.1)
    W = nmf.fit_transform(tfidf)
    nmf_clusters = W.argmax(axis=1)
    np.save(os.path.join(RES_DIR, "nmf_clusters.npy"), nmf_clusters)
    np.save(os.path.join(RES_DIR, "nmf_doc_topics.npy"), W)

    with open(os.path.join(RES_DIR, "nmf_results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"  Saved: nmf_results.json", flush=True)
    return results, nmf_clusters


# ============================================================
# K-Means clustering
# ============================================================
def train_kmeans(tfidf, k_values=[5, 8, 9, 10, 12, 15, 20]):
    print(f"\n=== K-Means Clustering (TF-IDF) ===", flush=True)
    # L2-normalize TF-IDF for spherical k-means
    from sklearn.preprocessing import Normalizer
    normalizer = Normalizer("l2")
    tfidf_norm = normalizer.fit_transform(tfidf)

    results = []
    best_clusters = None
    best_k = 9  # we have 9 sections
    for k in k_values:
        t0 = time.time()
        print(f"  K-Means k={k}...", flush=True, end=" ")
        km = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=300)
        clusters = km.fit_predict(tfidf_norm)
        # Silhouette (sample if too large)
        n_samples = tfidf_norm.shape[0]
        if n_samples > 1000:
            sample_idx = np.random.choice(n_samples, 1000, replace=False)
            sil = silhouette_score(tfidf_norm[sample_idx], clusters[sample_idx])
        else:
            sil = silhouette_score(tfidf_norm, clusters)
        inertia = km.inertia_
        elapsed = time.time() - t0
        print(f"silhouette={sil:.4f} inertia={inertia:.2f} elapsed={elapsed:.1f}s", flush=True)
        results.append({
            "k": k,
            "silhouette": float(sil),
            "inertia": float(inertia),
            "elapsed_sec": float(elapsed),
        })
        if k == best_k:
            best_clusters = clusters

    with open(os.path.join(RES_DIR, "kmeans_results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    np.save(os.path.join(RES_DIR, "kmeans_clusters.npy"), best_clusters)
    print(f"  Saved: kmeans_results.json (clusters for k={best_k})", flush=True)
    return results, best_clusters


# ============================================================
# Evaluate clusters vs section labels
# ============================================================
def evaluate_clusters(clusters, true_labels, name):
    nmi = normalized_mutual_info_score(true_labels, clusters)
    ari = adjusted_rand_score(true_labels, clusters)
    v = v_measure_score(true_labels, clusters)
    hom = homogeneity_score(true_labels, clusters)
    comp = completeness_score(true_labels, clusters)
    print(f"  {name:20s}  NMI={nmi:.4f}  ARI={ari:.4f}  V={v:.4f}  Hom={hom:.4f}  Comp={comp:.4f}", flush=True)
    return {
        "method": name,
        "nmi": float(nmi),
        "ari": float(ari),
        "v_measure": float(v),
        "homogeneity": float(hom),
        "completeness": float(comp),
    }


def main():
    print(f"Loading data...", flush=True)
    articles, docs_tokens, bow, tfidf, vocab_data = load_data()
    print(f"  Articles: {len(articles)}", flush=True)
    print(f"  TF-IDF shape: {tfidf.shape}", flush=True)
    true_labels = get_section_labels(articles)
    print(f"  True labels: {len(set(true_labels))} unique sections", flush=True)
    print(f"  Section distribution: {dict(Counter(true_labels))}", flush=True)

    all_evals = []

    # 1. LDA
    lda_results, lda_clusters = train_lda_gensim(docs_tokens)
    all_evals.append(evaluate_clusters(lda_clusters, true_labels, "LDA (best K)"))

    # 2. NMF
    nmf_results, nmf_clusters = train_nmf(tfidf)
    all_evals.append(evaluate_clusters(nmf_clusters, true_labels, "NMF (k=10)"))

    # 3. K-Means on TF-IDF
    kmeans_results, kmeans_clusters = train_kmeans(tfidf)
    all_evals.append(evaluate_clusters(kmeans_clusters, true_labels, "K-Means (k=9)"))

    # 4. SVD + K-Means (LSA-style)
    print(f"\n=== SVD + K-Means ===", flush=True)
    svd = TruncatedSVD(n_components=50, random_state=42)
    svd_features = svd.fit_transform(tfidf)
    km = KMeans(n_clusters=9, random_state=42, n_init=10)
    svd_clusters = km.fit_predict(svd_features)
    all_evals.append(evaluate_clusters(svd_clusters, true_labels, "SVD+KMeans (k=9)"))
    np.save(os.path.join(RES_DIR, "svd_kmeans_clusters.npy"), svd_clusters)

    # 5. Majority baseline (assign all to largest section)
    majority_label = Counter(true_labels).most_common(1)[0][0]
    majority_clusters = np.array([majority_label] * len(true_labels))
    all_evals.append(evaluate_clusters(majority_clusters, true_labels, "Majority baseline"))

    # Save all evaluations
    with open(os.path.join(RES_DIR, "all_evaluations.json"), "w", encoding="utf-8") as f:
        json.dump(all_evals, f, ensure_ascii=False, indent=2)
    print(f"\n=== All evaluations saved ===", flush=True)

    # Summary table
    print(f"\n=== FINAL SUMMARY ===", flush=True)
    print(f"{'Method':<22} {'NMI':>8} {'ARI':>8} {'V':>8} {'Hom':>8} {'Comp':>8}", flush=True)
    print("-" * 60, flush=True)
    for e in all_evals:
        print(f"{e['method']:<22} {e['nmi']:>8.4f} {e['ari']:>8.4f} {e['v_measure']:>8.4f} {e['homogeneity']:>8.4f} {e['completeness']:>8.4f}", flush=True)


if __name__ == "__main__":
    main()
