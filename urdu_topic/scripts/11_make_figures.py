"""
Generate all figures for the paper.
1. Articles per source (bar)
2. Articles per section (bar)
3. Article length distribution (hist)
4. LDA coherence vs K (line)
5. K-Means silhouette vs K (line)
6. Method comparison bar chart (NMI, ARI, V)
7. Top 10 words per LDA topic (heatmap or table)
8. Confusion matrix: predicted cluster vs true section
"""
import os, sys, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from collections import Counter
from sklearn.metrics import confusion_matrix
from sklearn.preprocessing import normalize

# Register Urdu-compatible font
fm.fontManager.addfont('/usr/share/fonts/truetype/freefont/FreeSerif.ttf')
fm.fontManager.addfont('/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf')
fm.fontManager.addfont('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['FreeSerif', 'DejaVu Serif']
plt.rcParams['axes.unicode_minus'] = False

RES_DIR = "/home/z/my-project/urdu_topic/results"
FIG_DIR = "/home/z/my-project/urdu_topic/figures"
os.makedirs(FIG_DIR, exist_ok=True)

# Color palette
COLORS = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
          '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']


def load_all():
    with open(os.path.join(RES_DIR, "processed_articles.json")) as f:
        articles = json.load(f)
    with open(os.path.join(RES_DIR, "lda_results.json")) as f:
        lda_results = json.load(f)
    with open(os.path.join(RES_DIR, "kmeans_results.json")) as f:
        kmeans_results = json.load(f)
    with open(os.path.join(RES_DIR, "nmf_results.json")) as f:
        nmf_results = json.load(f)
    with open(os.path.join(RES_DIR, "all_evaluations.json")) as f:
        all_evals = json.load(f)
    lda_clusters = np.load(os.path.join(RES_DIR, "lda_clusters.npy"))
    return articles, lda_results, kmeans_results, nmf_results, all_evals, lda_clusters


def fig1_articles_per_source(articles):
    sources = Counter(a["source"] for a in articles)
    labels = list(sources.keys())
    counts = [sources[s] for s in labels]
    fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
    bars = ax.bar(labels, counts, color=COLORS[:len(labels)])
    ax.set_ylabel("Number of Articles", fontsize=12)
    ax.set_title("Articles per Source", fontsize=14, fontweight='bold')
    ax.set_xlabel("Source", fontsize=12)
    for b, c in zip(bars, counts):
        ax.text(b.get_x() + b.get_width()/2, b.get_height() + 2, str(c),
                ha='center', va='bottom', fontsize=11, fontweight='bold')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.savefig(os.path.join(FIG_DIR, "fig1_articles_per_source.png"), dpi=150)
    plt.close()
    print("  Saved fig1")


def fig2_articles_per_section(articles):
    sections = Counter(a["section"] for a in articles)
    sorted_sec = sections.most_common()
    labels = [s for s, _ in sorted_sec]
    counts = [c for _, c in sorted_sec]
    fig, ax = plt.subplots(figsize=(9, 5), constrained_layout=True)
    bars = ax.barh(labels[::-1], counts[::-1], color=COLORS[2])
    ax.set_xlabel("Number of Articles", fontsize=12)
    ax.set_title("Articles per Section (auto-classified)", fontsize=14, fontweight='bold')
    for b, c in zip(bars, counts[::-1]):
        ax.text(b.get_width() + 1, b.get_y() + b.get_height()/2, str(c),
                ha='left', va='center', fontsize=11, fontweight='bold')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.savefig(os.path.join(FIG_DIR, "fig2_articles_per_section.png"), dpi=150)
    plt.close()
    print("  Saved fig2")


def fig3_length_dist(articles):
    lengths = [a["word_count"] for a in articles]
    fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
    ax.hist(lengths, bins=30, color=COLORS[3], edgecolor='white', alpha=0.85)
    ax.axvline(np.mean(lengths), color='black', linestyle='--', linewidth=2,
               label=f'Mean = {np.mean(lengths):.0f} words')
    ax.set_xlabel("Article Length (words)", fontsize=12)
    ax.set_ylabel("Frequency", fontsize=12)
    ax.set_title("Distribution of Article Lengths", fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.savefig(os.path.join(FIG_DIR, "fig3_length_distribution.png"), dpi=150)
    plt.close()
    print("  Saved fig3")


def fig4_lda_coherence(lda_results):
    ks = [r["k"] for r in lda_results]
    coh = [r["coherence"] for r in lda_results]
    perp = [r["perplexity"] for r in lda_results]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True)
    ax1.plot(ks, coh, 'o-', color=COLORS[0], linewidth=2, markersize=8)
    ax1.set_xlabel("Number of Topics (K)", fontsize=12)
    ax1.set_ylabel("Coherence (c_v)", fontsize=12)
    ax1.set_title("LDA Coherence vs K", fontsize=14, fontweight='bold')
    ax1.grid(alpha=0.3)
    best_k = ks[np.argmax(coh)]
    ax1.axvline(best_k, color='red', linestyle='--', alpha=0.5, label=f'Best K={best_k}')
    ax1.legend()
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)

    ax2.plot(ks, perp, 's-', color=COLORS[1], linewidth=2, markersize=8)
    ax2.set_xlabel("Number of Topics (K)", fontsize=12)
    ax2.set_ylabel("Perplexity", fontsize=12)
    ax2.set_title("LDA Perplexity vs K", fontsize=14, fontweight='bold')
    ax2.grid(alpha=0.3)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    plt.savefig(os.path.join(FIG_DIR, "fig4_lda_coherence.png"), dpi=150)
    plt.close()
    print("  Saved fig4")


def fig5_kmeans_silhouette(kmeans_results):
    ks = [r["k"] for r in kmeans_results]
    sil = [r["silhouette"] for r in kmeans_results]
    inertia = [r["inertia"] for r in kmeans_results]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True)
    ax1.plot(ks, sil, 'o-', color=COLORS[2], linewidth=2, markersize=8)
    ax1.set_xlabel("Number of Clusters (K)", fontsize=12)
    ax1.set_ylabel("Silhouette Score", fontsize=12)
    ax1.set_title("K-Means Silhouette vs K", fontsize=14, fontweight='bold')
    ax1.grid(alpha=0.3)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)

    ax2.plot(ks, inertia, 's-', color=COLORS[4], linewidth=2, markersize=8)
    ax2.set_xlabel("Number of Clusters (K)", fontsize=12)
    ax2.set_ylabel("Inertia", fontsize=12)
    ax2.set_title("K-Means Elbow", fontsize=14, fontweight='bold')
    ax2.grid(alpha=0.3)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    plt.savefig(os.path.join(FIG_DIR, "fig5_kmeans_metrics.png"), dpi=150)
    plt.close()
    print("  Saved fig5")


def fig6_method_comparison(all_evals):
    # Use only the round-1 methods (LDA, NMF, K-Means, SVD, Majority)
    # Plus best round-2 methods
    methods_to_show = [
        "LDA best K=10",
        "NMF k=9",
        "K-Means k=9",
        "SVD+KMeans (k=9)",
        "Spectral k=10",
        "LDA-features+KMeans k=9",
        "TF-IDF+LDA PCA+KMeans k=9",
        "Agglomerative k=12",
        "Majority baseline",
    ]
    seen = set()
    selected = []
    for m in methods_to_show:
        for e in all_evals:
            if e["method"] == m and m not in seen:
                selected.append(e)
                seen.add(m)
                break

    names = [e["method"] for e in selected]
    nmis = [e["nmi"] for e in selected]
    aris = [e["ari"] for e in selected]
    vs = [e["v_measure"] for e in selected]

    x = np.arange(len(names))
    width = 0.27
    fig, ax = plt.subplots(figsize=(13, 6), constrained_layout=True)
    ax.bar(x - width, nmis, width, label='NMI', color=COLORS[0])
    ax.bar(x, aris, width, label='ARI', color=COLORS[1])
    ax.bar(x + width, vs, width, label='V-measure', color=COLORS[2])
    ax.set_ylabel("Score", fontsize=12)
    ax.set_title("Clustering Performance Comparison", fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=30, ha='right', fontsize=9)
    ax.legend(fontsize=11)
    ax.grid(axis='y', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.savefig(os.path.join(FIG_DIR, "fig6_method_comparison.png"), dpi=150)
    plt.close()
    print("  Saved fig6")


def fig7_lda_topics_heatmap(lda_results):
    # Show top words for best K (=10)
    best = max(lda_results, key=lambda r: r["coherence"])
    topics = best["topics"]
    K = best["k"]
    # Build a matrix of top-10 words per topic for visualization (just show first 8 topics in a grid)
    n_show = min(8, K)
    cols = 2
    rows = (n_show + 1) // 2
    fig, axes = plt.subplots(rows, cols, figsize=(12, 2.5 * rows), constrained_layout=True)
    if rows == 1:
        axes = [axes]
    for i in range(n_show):
        r, c = i // cols, i % cols
        ax = axes[r][c] if rows > 1 else axes[c]
        words = topics[i]
        weights = list(range(10, 0, -1))  # just visualize top-10 with decreasing weight
        ax.barh(words[::-1], weights[::-1], color=COLORS[i % len(COLORS)])
        ax.set_title(f"Topic {i+1}", fontsize=12, fontweight='bold')
        ax.set_xlabel("Rank Weight", fontsize=9)
        ax.tick_params(axis='y', labelsize=9)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
    # Hide unused subplots
    for i in range(n_show, rows * cols):
        r, c = i // cols, i % cols
        ax = axes[r][c] if rows > 1 else axes[c]
        ax.axis('off')
    plt.suptitle(f"LDA Top-10 Words per Topic (K={K}, coherence={best['coherence']:.3f})",
                 fontsize=13, fontweight='bold')
    plt.savefig(os.path.join(FIG_DIR, "fig7_lda_topics.png"), dpi=150)
    plt.close()
    print("  Saved fig7")


def fig8_confusion_matrix(articles, lda_clusters):
    true_labels = np.array([a["section"] for a in articles])
    # Build confusion matrix
    sections = sorted(set(true_labels))
    n_sec = len(sections)
    n_clusters = len(set(lda_clusters))
    cm = np.zeros((n_sec, n_clusters), dtype=int)
    sec_to_idx = {s: i for i, s in enumerate(sections)}
    for tl, pc in zip(true_labels, lda_clusters):
        cm[sec_to_idx[tl], pc] += 1
    # Normalize per row
    cm_norm = normalize(cm.astype(float), norm='l1', axis=1)

    fig, ax = plt.subplots(figsize=(10, 6), constrained_layout=True)
    im = ax.imshow(cm_norm, cmap='Blues', aspect='auto')
    ax.set_xticks(range(n_clusters))
    ax.set_xticklabels([f"C{i}" for i in range(n_clusters)], fontsize=10)
    ax.set_yticks(range(n_sec))
    ax.set_yticklabels(sections, fontsize=10)
    ax.set_xlabel("Predicted Cluster", fontsize=12)
    ax.set_ylabel("True Section", fontsize=12)
    ax.set_title("LDA Cluster vs True Section (row-normalized)", fontsize=14, fontweight='bold')
    # Add count text
    for i in range(n_sec):
        for j in range(n_clusters):
            if cm[i, j] > 0:
                color = "white" if cm_norm[i, j] > 0.5 else "black"
                ax.text(j, i, str(cm[i, j]), ha='center', va='center',
                        color=color, fontsize=8, fontweight='bold')
    plt.colorbar(im, ax=ax, label='Fraction of Section')
    plt.savefig(os.path.join(FIG_DIR, "fig8_confusion_matrix.png"), dpi=150)
    plt.close()
    print("  Saved fig8")


def main():
    print("Generating figures...", flush=True)
    articles, lda_results, kmeans_results, nmf_results, all_evals, lda_clusters = load_all()
    print(f"  Loaded: {len(articles)} articles, {len(all_evals)} evaluations", flush=True)

    fig1_articles_per_source(articles)
    fig2_articles_per_section(articles)
    fig3_length_dist(articles)
    fig4_lda_coherence(lda_results)
    fig5_kmeans_silhouette(kmeans_results)
    fig6_method_comparison(all_evals)
    fig7_lda_topics_heatmap(lda_results)
    fig8_confusion_matrix(articles, lda_clusters)

    print(f"\nAll figures saved to: {FIG_DIR}", flush=True)
    print(os.listdir(FIG_DIR), flush=True)


if __name__ == "__main__":
    main()
