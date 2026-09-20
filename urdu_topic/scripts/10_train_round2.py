"""
Round 2 — fix NMF + add stronger methods:
- NMF without heavy regularization (the alpha_W=0.1 was killing it)
- Agglomerative clustering with cosine linkage
- Combined LDA + KMeans (consensus)
- FastText-style averaged word vectors (using BoW + LDA topics as features)
"""
import os, sys, json, time, warnings
import numpy as np
import scipy.sparse as sp
from collections import Counter
from sklearn.decomposition import NMF, TruncatedSVD, PCA
from sklearn.cluster import KMeans, AgglomerativeClustering, SpectralClustering
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import Normalizer, LabelEncoder
from sklearn.metrics import (
    normalized_mutual_info_score, adjusted_rand_score,
    v_measure_score, homogeneity_score, completeness_score,
    silhouette_score
)
warnings.filterwarnings("ignore")

RES_DIR = "/home/z/my-project/urdu_topic/results"


def load_data():
    with open(os.path.join(RES_DIR, "processed_articles.json")) as f:
        articles = json.load(f)
    bow = sp.load_npz(os.path.join(RES_DIR, "bow.npz"))
    tfidf = sp.load_npz(os.path.join(RES_DIR, "tfidf.npz"))
    with open(os.path.join(RES_DIR, "vocab.json")) as f:
        vocab_data = json.load(f)
    return articles, bow, tfidf, vocab_data


def evaluate(clusters, true_labels, name):
    nmi = normalized_mutual_info_score(true_labels, clusters)
    ari = adjusted_rand_score(true_labels, clusters)
    v = v_measure_score(true_labels, clusters)
    hom = homogeneity_score(true_labels, clusters)
    comp = completeness_score(true_labels, clusters)
    print(f"  {name:<35}  NMI={nmi:.4f}  ARI={ari:.4f}  V={v:.4f}", flush=True)
    return {"method": name, "nmi": float(nmi), "ari": float(ari),
            "v_measure": float(v), "homogeneity": float(hom), "completeness": float(comp)}


def main():
    articles, bow, tfidf, vocab_data = load_data()
    true_labels = np.array([a["section"] for a in articles])
    print(f"Loaded: {len(articles)} articles, {len(set(true_labels))} sections", flush=True)

    # Normalize TF-IDF
    normalizer = Normalizer("l2")
    tfidf_norm = normalizer.fit_transform(tfidf)

    results = []

    # === 1. NMF (fixed — no heavy regularization) ===
    print(f"\n=== NMF (no regularization) ===", flush=True)
    for k in [9, 10, 12, 15]:
        nmf = NMF(n_components=k, random_state=42, max_iter=500, init="nndsvd")
        W = nmf.fit_transform(tfidf)
        clusters = W.argmax(axis=1)
        r = evaluate(clusters, true_labels, f"NMF k={k}")
        results.append(r)
        np.save(os.path.join(RES_DIR, f"nmf_fixed_k{k}_clusters.npy"), clusters)

    # === 2. Agglomerative clustering (cosine) ===
    print(f"\n=== Agglomerative Clustering (cosine) ===", flush=True)
    # Need dense for agglomerative
    tfidf_dense = tfidf_norm.toarray()
    for k in [9, 10, 12]:
        ac = AgglomerativeClustering(n_clusters=k, metric="cosine", linkage="average")
        clusters = ac.fit_predict(tfidf_dense)
        r = evaluate(clusters, true_labels, f"Agglomerative k={k}")
        results.append(r)

    # === 3. Spectral clustering ===
    print(f"\n=== Spectral Clustering ===", flush=True)
    for k in [9, 10]:
        try:
            sc = SpectralClustering(n_clusters=k, affinity="cosine", random_state=42, n_init=10)
            clusters = sc.fit_predict(tfidf_dense)
            r = evaluate(clusters, true_labels, f"Spectral k={k}")
            results.append(r)
        except Exception as e:
            print(f"  Spectral k={k} failed: {e}", flush=True)

    # === 4. LDA + K-Means ensemble (using LDA doc-topic as features) ===
    print(f"\n=== LDA + K-Means (consensus) ===", flush=True)
    lda_doc_topics = np.load(os.path.join(RES_DIR, "lda_doc_topics.npy"))
    for k in [9, 10]:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        clusters = km.fit_predict(lda_doc_topics)
        r = evaluate(clusters, true_labels, f"LDA-features+KMeans k={k}")
        results.append(r)

    # === 5. Combined features: TF-IDF + LDA topics ===
    print(f"\n=== TF-IDF + LDA combined ===", flush=True)
    combined = np.hstack([tfidf_norm.toarray(), lda_doc_topics])
    # PCA to reduce dim
    pca = PCA(n_components=50, random_state=42)
    combined_pca = pca.fit_transform(combined)
    km = KMeans(n_clusters=9, random_state=42, n_init=10)
    clusters = km.fit_predict(combined_pca)
    r = evaluate(clusters, true_labels, "TF-IDF+LDA PCA+KMeans k=9")
    results.append(r)

    # === 6. K-Means with more clusters (k=15, k=20) — better granularity ===
    print(f"\n=== K-Means higher K ===", flush=True)
    for k in [15, 20]:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        clusters = km.fit_predict(tfidf_norm)
        r = evaluate(clusters, true_labels, f"K-Means k={k}")
        results.append(r)

    # === 7. Best LDA model evaluation (already done, include for table) ===
    lda_clusters = np.load(os.path.join(RES_DIR, "lda_clusters.npy"))
    r = evaluate(lda_clusters, true_labels, "LDA best K=10")
    results.append(r)

    # Save all
    existing = []
    if os.path.exists(os.path.join(RES_DIR, "all_evaluations.json")):
        with open(os.path.join(RES_DIR, "all_evaluations.json")) as f:
            existing = json.load(f)
    existing.extend(results)
    with open(os.path.join(RES_DIR, "all_evaluations.json"), "w") as f:
        json.dump(existing, f, indent=2)

    # Print final ranking
    print(f"\n=== FINAL RANKING (by NMI) ===", flush=True)
    sorted_results = sorted(results, key=lambda r: -r["nmi"])
    print(f"{'Method':<40} {'NMI':>8} {'ARI':>8} {'V':>8}", flush=True)
    print("-" * 70, flush=True)
    for r in sorted_results:
        print(f"{r['method']:<40} {r['nmi']:>8.4f} {r['ari']:>8.4f} {r['v_measure']:>8.4f}", flush=True)


if __name__ == "__main__":
    main()
