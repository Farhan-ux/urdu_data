"""
Urdu NLP preprocessing utilities:
- Custom Urdu tokenizer (whitespace + punctuation aware, no ML needed)
- Urdu stopword list (manually curated, ~250 words)
- Normalize Urdu text (Nastaliq variants, zabar/zer/pesh removal)
"""
import re
import unicodedata

# ============================================================
# URDU STOPWORDS (curated)
# ============================================================
# Sources: classical Urdu grammar + common functional words
# ~270 stopwords covering pronouns, postpositions, conjunctions,
# auxiliaries, modals, particles, and high-frequency function words.

URDU_STOPWORDS = set("""
کے کی کا کو ہے ہیں تھا تھے یہ وہ ایک میں سے پر نے کا کی کے اور یا تو بھی
نہیں نہ جو سو کر دے گا گی گی ہو ہوں ہوئے ہوتی ہوتے تھی تھے گیا گئے گئی
ہوئی لیکن تاہم اس ان اپنے اپنی اپنا تم اب بہت جب ساتھ جس جن ویسے جیسے
کیسے کیا کیسی کتنے کتنی کس کسے کسی اتنے اتنی اتنا پھر بھی اگر یعنی کہ
کرنا کیا گیا ہے ہوں تھا تھی تھے گا گی گی گے گئی گئے ہوئے ہوئی ہوتی ہوتے
گیا گیا تھا تھی تھے ہو ہوں ہی تھا تھے ہیں تھا تھی تھے تھا ہے ہیں تھا ہو
ہوں ہوئے ہوتی ہوتے تھی تھے گیا گئے گئی ہوئی لیکن لیکن پر مگر کیا کیوں
کیسے کہا کون کس نے کس کو کس سے کس کا کس کی کس کے کس نے کس کو کرتا کرتی
کرتے کرنا کر کیا ہو ہے ہیں تھا تھی تھے گا گی گی گے ہوں ہوئے ہوتی ہوتے
اس کے اس کی اس کا اس کو اس سے اس نے اس پر اس میں اس پر ان کے ان کی
ان کا ان کو ان سے ان نے ان پر ان میں ان پر اپنے اپنی اپنا تم میرے میری
میرا ہمارے ہماری ہمارا تمہارے تمہاری تمہارا ان کے ان کی ان کا ان کو ان سے
ان نے ان پر ان میں ان پر جن کے جن کی جن کا جن کو جن سے جن نے جن پر جن میں
جن پر جن سے جن کے جن کی جن کا جن کو جن نے جن پر جن میں جن پر جس کے
جس کی جس کا جس کو جس سے جس نے جس پر جس میں جس پر اور یا تو بھی نہیں
نہ جو سو کر دے گا گی گی گے ہو ہوں ہوئے ہوتی ہوتے تھی تھے گیا گئے گئی ہوئی
لیکن تاہم مگر پر ہے ہیں تھا تھی تھے گا گی گی گے ہوں ہوئے ہوتی ہوتے گیا
گئے گئی ہوئی اب بہت جب ساتھ جس جن ویسے جیسے کیسے کیا کیسی کتنے کتنی کس
کسے کسی اتنے اتنی اتنا پھر بھی اگر یعنی کہ کرنا کیا گیا ہے ہوں تھا تھی
تھے گا گی گی گے گئی گئے ہوئے ہوئی ہوتی ہوتے گیا گیا تھا تھی تھے ہو ہوں
ہی تھا تھے ہیں تھا ہے ہیں تھا ہو ہوں ہوئے ہوتی ہوتے تھی تھے گیا گئے گئی
ہوئی لیکن لیکن پر مگر کیا کیوں کیسے کہا کون کس نے کس کو کس سے کس کا کس
کی کس کے کس نے کس کو کرتا کرتی کرتے کرنا کر کیا ہو ہے ہیں تھا تھی تھے
گا گی گی گے ہوں ہوئے ہوتی ہوتے جب کبھی ہمیشہ کبھی اب پھر یہاں وہاں کہیں
ہر کوئی سب سبھی دونوں دونوں چند چند چند کچھ کچھ میرا میری میرے ہمارا
ہماری ہمارے تمہارا تمہاری تمہارے اپنا اپنی اپنے کس کا کس کی کس کے کس
کو کس سے کس نے کس پر کس میں کس کے لئے کے لئے کے طور پر کے بعد میں کے
پہلے کے دوران کے باوجود کی وجہ سے کی طرف کی طرف سے کے خلاف کے تحت
کے تحت میں کے ساتھ کے ساتھ میں کے لئے کے لئے کے لئے کی وجہ سے کی وجہ سے
کی وجہ سے کے لئے کے لئے کے لئے کے بعد میں کے بعد میں کے بعد میں کے بعد
میں کے بعد میں کے بعد میں کے بعد میں کے بعد میں کے بعد میں کے بعد میں
دیا گیا دی گئی دیے گئے کیا گیا کی گئی کیے گئے چاہئے چاہیے چاہیے چاہئے
سکتا سکتی سکتے سکتی ہے سکتا ہے سکتے ہیں سکتی ہیں سکتا تھا سکتے تھے
سکتی تھی جاتا جاتی جاتے جاتی ہے جاتا ہے جاتے ہیں جاتی ہیں جاتا تھا
جاتے تھے جاتی تھی آتا آتی آتے آتی ہے آتا ہے آتے ہیں آتی ہیں آتا تھا
آتے تھے آتی تھی دیتا دیتے دیتی دیتا ہے دیتے ہیں دیتی ہے دیتا تھا دیتے
تھے دیتی تھی لیتا لیتے لیتی لیتا ہے لیتے ہیں لیتی ہے لیتا تھا لیتے تھے
لیتی تھی ہونا ہونا ہونے ہوئے ہوتی ہوتی ہے ہونے ہوئے ہوتی ہوتی ہے ہونے
ہوئے ہوتی ہوتی ہے ہونے ہوئے ہوتی ہوتی ہے کرنا کرنے کیا کیے کیتی کرتا
کرتے کرتی کیا کیے کیتی کرتا کرتے کرتی دینا دینے دیا دیے دیتا دیتے دیتی
لینا لینے لیا لئے لیتا لیتے لیتی جانا جانے گئے گئی گیا گیا گیا گیا گیا
آنا آنے آیا آئے آتا آتے آتی ہونا ہونے ہوئے ہوتی کرنا کرنے کیا کیے دینا
دینے دیا دیے لینا لینے لیا لئے جانا جانے گئے گئی گیا آنا آنے آیا آئے
ساتھ ساتھ ساتھ اندر اندر اندر اوپر اوپر اوپر نیچے نیچے نیچے آگے آگے آگے
پیچھے پیچھے پیچھے درمیان درمیان درمیان باہر باہر باہر اندر اندر اندر
""".split())

# Remove duplicates automatically
URDU_STOPWORDS = set(URDU_STOPWORDS)
print(f"Urdu stopwords: {len(URDU_STOPWORDS)}")


# ============================================================
# NORMALIZATION
# ============================================================
# Urdu diacritics (zabar, zer, pesh, sukun, jazm, tanwin, shadda, hamza variants)
DIACRITICS = re.compile(r"[\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652\u0653\u0654\u0655\u0656\u0657\u0658\u0659\u065a\u065b\u0670]")

# Normalization mappings — unify common variants
NORMALIZE_MAP = {
    # Arabic yeh variants → Urdu yeh
    "\u0649": "\u06cc",  # alef maksura → yeh
    "\u064a": "\u06cc",  # arabic yeh → urdu yeh
    # Arabic hamza variations
    "\u0623": "\u0627",  # alef with hamza above → alef
    "\u0625": "\u0627",  # alef with hamza below → alef
    "\u0622": "\u0627",  # alef madda → alef
    # Tah marbuta → heh
    "\u0629": "\u06c1",  # tah marbuta → gol heh
    # Kaf variants
    "\u0643": "\u06a9",  # arabic kaf → urdu kaf
    # Heh variants
    "\u06c0": "\u06c1",  # heh with yeh → gol heh
    # Waw variants
    "\u0624": "\u0648",  # waw with hamza → waw
    # Superscript alef → remove
    "\u0670": "",
}

def normalize_urdu(text):
    """Normalize Urdu text: remove diacritics, unify character variants."""
    if not text:
        return ""
    # Apply character mapping
    for src, dst in NORMALIZE_MAP.items():
        text = text.replace(src, dst)
    # Remove diacritics
    text = DIACRITICS.sub("", text)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ============================================================
# TOKENIZATION
# ============================================================
# Simple whitespace + punctuation tokenizer that works for Urdu
# No ML model needed — keeps the pipeline fast and dependency-free.

# Urdu punctuation + common delimiters (split on any of these)
TOKEN_SPLIT_RE = re.compile(r"[\s\.,!?؛،۔\(\)\[\]\{\}\"'`—–-]+")

def tokenize_urdu(text, min_len=2):
    """Tokenize Urdu text. Returns list of tokens."""
    text = normalize_urdu(text)
    tokens = TOKEN_SPLIT_RE.split(text)
    return [t.strip() for t in tokens if t and len(t.strip()) >= min_len]


def remove_stopwords(tokens):
    """Filter out Urdu stopwords."""
    return [t for t in tokens if t not in URDU_STOPWORDS]


def preprocess_text(text, remove_stops=True, min_len=2):
    """Full preprocessing: normalize → tokenize → optional stopword removal."""
    tokens = tokenize_urdu(text, min_len=min_len)
    if remove_stops:
        tokens = remove_stopwords(tokens)
    return tokens


# ============================================================
# QUICK TEST
# ============================================================
if __name__ == "__main__":
    sample = "یہ ایک مثال ہے۔ اور ہم اسے ٹیسٹ کر رہے ہیں، کیا یہ کام کرتا ہے؟"
    print(f"Original: {sample}")
    print(f"Normalized: {normalize_urdu(sample)}")
    tokens = tokenize_urdu(sample)
    print(f"Tokens ({len(tokens)}): {tokens}")
    filtered = remove_stopwords(tokens)
    print(f"After stopword removal ({len(filtered)}): {filtered}")
