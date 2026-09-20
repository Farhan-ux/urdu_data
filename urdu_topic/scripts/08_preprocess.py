"""
Preprocess all articles:
- Clean text
- Re-label sections using URL + title heuristics
- Tokenize using Urdu tokenizer + stopword removal
- Build vocabulary (filter min_df=5, max_df=0.5)
- Output: processed corpus + vocabulary + doc-term matrix (BoW + TF-IDF)
"""
import os, sys, json, re, time
from collections import Counter, defaultdict

sys.path.insert(0, "/home/z/my-project/urdu_topic/scripts")
from urdu_preprocess import preprocess_text, normalize_urdu, URDU_STOPWORDS

DATA_DIR = "/home/z/my-project/urdu_topic/data"
OUT_DIR = "/home/z/my-project/urdu_topic/results"
os.makedirs(OUT_DIR, exist_ok=True)


# ============================================================
# SECTION RE-LABELING
# ============================================================
# Map URL patterns + keyword heuristics to canonical sections

# Keywords per section (Urdu)
SECTION_KEYWORDS = {
    "pakistan": ["پاکستان", "کراچی", "لاہور", "اسلام آباد", "پنجاب", "سندھ", "خیبر", "بلوچستان", "پشاور", "ایوب", "قومی اسمبلی", "وزیراعظم", "صدر"],
    "world": ["دنیا", "امریکہ", "امریکی", "چین", "چینی", "بھارت", "ہندوستان", "روسی", "روس", "یورپ", "یورپی", "افغانستان", "افغان", "ایران", "ترکی", "برطانیہ", "اسرائیل", "فلسطین", "غزہ", "لبنان", "یوکرین", " اقوام متحدہ"],
    "sports": ["کرکٹ", "فٹبال", "ہاکی", "کھیل", "کھیلوں", "میچ", "ٹورنامنٹ", "پاکستان کرکٹ", "ایشین گیمز", "اولمپک", "ورلڈ کپ", "بیٹسمین", "بولر", "پلیئر", "ٹیم", "اسکور", "ون ڈے", "ٹیسٹ", "ٹی ٹوئنٹی", "T20", "PSL"],
    "entertainment": ["فلم", "اداکار", "اداکارہ", "بالی ووڈ", "ہالی ووڈ", "ٹی وی", "ڈرامہ", "موسیقی", "گانے", "گلوکار", "گنگتانا", "شوز", "نیٹ فلکس", "سنیما", " میوزک"],
    "science": ["سائنس", "ٹیکنالوجی", "خلائی", "ناسا", "سپیس ایکس", "مریخ", "چاند", "حیاتیاتی", "کیمیکل", "فزکس", "طب", "تحقیق", "سائنسی", "AI", "مصنوعی ذہانت"],
    "business": ["ڈالر", "روپے", "اسٹاک", "مارکیٹ", "تجارت", "معیشت", "بینک", "سرمایہ کاری", "آمدنی", "خرچ", "بجٹ", " مالیاتی", "کرنسی", "ایکسپورٹ", "امپورٹ", "GDP", "IMF"],
    "lifestyle": ["خوراک", "پکوان", "فیشن", "خوبصورتی", "صحت", "ورزش", "یوگا", "تعلم", "باغ", "سفر", "ٹور", "ہوٹل", "رہائش", "کھانا", "لائف سٹائل"],
    "crime": ["قتل", "ڈکیتی", "چوری", "جرم", "پولیس", "ایف آئی آر", "عدالت", "جج", "وکیل", "تفتیش", "گرفتار", "مقدمہ", "سزا", "جرم"],
}


def classify_section(article):
    """Determine section from URL pattern first, then from title+body keywords."""
    url = article.get("url", "")
    title = article.get("title", "")
    body = article.get("body", "")[:1000]
    text = title + " " + body

    # URL-based detection first
    if "express.pk" in url:
        # Express URL: /story/<id>/<slug>
        # Look at slug for keywords
        m = re.search(r"/story/\d+/([a-z0-9-]+)", url)
        if m:
            slug = m.group(1)
            # Check for category hints in slug
            if "pakistan" in slug or "karachi" in slug or "lahore" in slug:
                return "pakistan"
            if "cricket" in slug or "sports" in slug or "match" in slug or "hockey" in slug:
                return "sports"
            if "trump" in slug or "israel" in slug or "ukraine" in slug or "world" in slug:
                return "world"
            if "bollywood" in slug or "actor" in slug or "film" in slug:
                return "entertainment"
            if "ai-" in slug or "tech" in slug or "science" in slug:
                return "science"
            if "dollar" in slug or "stock" in slug or "market" in slug or "budget" in slug:
                return "business"
    if "jang.com.pk" in url:
        # Jang URL: /news/<id> — no section info; classify from text
        pass
    if "nawaiwaqt" in url:
        # Date-based URLs — need text classification
        pass
    if "bbc.com/urdu" in url:
        # BBC URL: /urdu/<section>-<id>
        path = url.split("bbc.com/urdu/")[1].split("-")[0] if "bbc.com/urdu/" in url else ""
        if path in ["pakistan", "world", "sport", "science", "business", "entertainment"]:
            return "pakistan" if path == "pakistan" else path
        if path == "sport":
            return "sports"

    # Text-based classification: count keyword hits per section
    section_scores = defaultdict(int)
    for section, keywords in SECTION_KEYWORDS.items():
        for kw in keywords:
            # Count occurrences
            count = text.count(kw)
            section_scores[section] += count

    if max(section_scores.values()) > 0:
        return max(section_scores.items(), key=lambda x: x[1])[0]

    return "general"


# ============================================================
# MAIN PREPROCESSING
# ============================================================
def main():
    print("Loading articles...", flush=True)
    with open(os.path.join(DATA_DIR, "all_articles.json")) as f:
        articles = json.load(f)
    print(f"  Loaded: {len(articles)} articles", flush=True)

    # Deduplicate by URL
    seen_urls = set()
    unique_articles = []
    for a in articles:
        u = a.get("url", "")
        if u and u not in seen_urls:
            seen_urls.add(u)
            unique_articles.append(a)
    print(f"  After dedup: {len(unique_articles)} articles", flush=True)

    # Filter articles that are too short or non-Urdu
    cleaned = []
    for a in unique_articles:
        body = a.get("body", "")
        title = a.get("title", "")
        if not body or len(body) < 200:
            continue
        # Quick Urdu check: at least 30% of body chars should be Urdu/Arabic
        urdu_chars = sum(1 for c in body if "\u0600" <= c <= "\u06FF")
        alpha_chars = sum(1 for c in body if c.isalpha())
        if alpha_chars == 0 or urdu_chars / max(1, alpha_chars) < 0.3:
            continue
        # Re-classify section
        section = classify_section(a)
        cleaned.append({
            "url": a["url"],
            "title": title,
            "section": section,
            "body": body,
            "source": a["source"],
            "word_count": len(body.split()),
        })
    print(f"  After filtering: {len(cleaned)} articles", flush=True)

    # Section distribution
    sec_dist = Counter(a["section"] for a in cleaned)
    print(f"\nSection distribution:", flush=True)
    for s, c in sec_dist.most_common():
        print(f"  {c:5d}  {s}", flush=True)

    # Tokenize all articles
    print(f"\nTokenizing...", flush=True)
    t0 = time.time()
    docs_tokens = []
    for i, a in enumerate(cleaned):
        text = a["title"] + " " + a["body"]
        tokens = preprocess_text(text, remove_stops=True, min_len=2)
        docs_tokens.append(tokens)
        if (i + 1) % 100 == 0:
            print(f"  [{i+1}/{len(cleaned)}] elapsed={time.time()-t0:.1f}s", flush=True)

    # Filter out empty docs
    keep_idx = [i for i, t in enumerate(docs_tokens) if len(t) >= 10]
    cleaned = [cleaned[i] for i in keep_idx]
    docs_tokens = [docs_tokens[i] for i in keep_idx]
    print(f"  After tokenization filter (>=10 tokens): {len(cleaned)} articles", flush=True)

    # Build vocabulary with min_df=5, max_df=0.5
    print(f"\nBuilding vocabulary...", flush=True)
    N = len(docs_tokens)
    df = Counter()
    for toks in docs_tokens:
        for w in set(toks):
            df[w] += 1
    min_df = 5
    max_df = int(0.5 * N)
    vocab = [w for w, c in df.items() if c >= min_df and c <= max_df]
    vocab_idx = {w: i for i, w in enumerate(sorted(vocab))}
    print(f"  Vocab size: {len(vocab)} (min_df={min_df}, max_df={max_df})", flush=True)

    # Build BoW + TF-IDF matrices
    print(f"Building BoW + TF-IDF...", flush=True)
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer

    # Use sklearn for TF-IDF (faster than manual)
    docs_text = [" ".join(toks) for toks in docs_tokens]

    # CountVectorizer with our vocab
    cv = CountVectorizer(vocabulary=vocab_idx, tokenizer=lambda x: x.split(), lowercase=False, token_pattern=None)
    bow = cv.fit_transform(docs_text)
    print(f"  BoW shape: {bow.shape}", flush=True)

    # TF-IDF
    tfidf_v = TfidfVectorizer(vocabulary=vocab_idx, tokenizer=lambda x: x.split(), lowercase=False, token_pattern=None, norm="l2", sublinear_tf=True)
    tfidf = tfidf_v.fit_transform(docs_text)
    print(f"  TF-IDF shape: {tfidf.shape}", flush=True)

    # Save everything
    print(f"\nSaving artifacts...", flush=True)
    # Articles with sections
    out_articles = os.path.join(OUT_DIR, "processed_articles.json")
    with open(out_articles, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)
    print(f"  Articles: {out_articles}")

    # Tokenized docs
    out_tokens = os.path.join(OUT_DIR, "docs_tokens.json")
    with open(out_tokens, "w", encoding="utf-8") as f:
        json.dump(docs_tokens, f, ensure_ascii=False)
    print(f"  Tokens: {out_tokens}")

    # Vocabulary
    out_vocab = os.path.join(OUT_DIR, "vocab.json")
    with open(out_vocab, "w", encoding="utf-8") as f:
        json.dump({
            "vocab": sorted(vocab),
            "vocab_idx": vocab_idx,
            "df": dict(df),
            "N_docs": N,
            "min_df": min_df,
            "max_df": max_df,
        }, f, ensure_ascii=False, indent=2)
    print(f"  Vocab: {out_vocab}")

    # Save matrices as npz
    import scipy.sparse
    scipy.sparse.save_npz(os.path.join(OUT_DIR, "bow.npz"), bow)
    scipy.sparse.save_npz(os.path.join(OUT_DIR, "tfidf.npz"), tfidf)
    print(f"  BoW + TF-IDF matrices saved")

    # Summary stats
    total_tokens = sum(len(t) for t in docs_tokens)
    avg_tokens = total_tokens / len(docs_tokens)
    print(f"\n=== SUMMARY ===")
    print(f"  Total articles: {len(cleaned)}")
    print(f"  Total tokens (after preprocessing): {total_tokens:,}")
    print(f"  Avg tokens/doc: {avg_tokens:.0f}")
    print(f"  Vocabulary size: {len(vocab)}")
    print(f"  Sections: {len(sec_dist)}")


if __name__ == "__main__":
    main()
