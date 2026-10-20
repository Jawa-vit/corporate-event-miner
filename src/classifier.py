"""
Task (b): Classify whether an article is about a Corporate Event.

Hybrid Machine-Learning & Heuristic Architecture:
  1. Title-weighted Document Representation (prioritizes current headline intent over historical body mentions)
  2. Sublinear TF-IDF (word unigrams + bigrams) + Balanced Logistic Regression
  3. Domain Heuristic Override: Detects hostile takeover resistance signals (poison pill, unsolicited bid)
  4. Contextual Guard Filters: Suppresses false positives from routine earnings, volume reports,
     and market indices that merely mention historical M&A in passing.
"""
import csv
import os
import re

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from . import seed_data

MODEL_PATH = "output/event_classifier.joblib"
TRAIN_PATH = "data/training_data.csv"

# Heuristic indicator for hostile bids vs friendly acquisitions
HOSTILE_RE = re.compile(
    r"hostile|unsolicited|poison pill|rejects? (?:the )?(?:bid|offer)|"
    r"fend(?:s|ing)? off|resist(?:s|ing)? the (?:bid|offer)|tender offer directly|"
    r"proxy fight|unwelcome offer", re.I
)

# Common non-event headline indicators (earnings, macro trends, commodity prices)
NO_EVENT_HEADLINE_RE = re.compile(
    r"\b(posts? record volumes?|reports? (?:quarterly )?(?:net )?profit|"
    r"profit (?:rises?|falls?|jumps?|dips?)|shares? (?:rally|slip|fall|jump|rise)|"
    r"sensex|nifty|nasdaq|dow jones|inflation|oil prices?|gold prices?|"
    r"interim dividend|weakens? against the dollar|interest rates? unchanged)\b", re.I
)

# Active transaction verbs in headlines that confirm real current events
EVENT_TRIGGER_HEADLINE_RE = re.compile(
    r"\b(acquire[sd]?|buy|buys|bought|takeover|merger?|merge[sd]?|sell[s]?|sold|divest[s]?|"
    r"appoint[s]?|name[s]?|resign[s]?|steps? down|ipo|initial public offering|files? draft)\b", re.I
)


def _load(path):
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return [r["text"] for r in rows], [r["label"] for r in rows]


def train(verbose=True):
    if not os.path.exists(TRAIN_PATH):
        seed_data.build(TRAIN_PATH)
    X, y = _load(TRAIN_PATH)
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    
    model = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), lowercase=True, sublinear_tf=True, min_df=1)),
        ("clf", LogisticRegression(max_iter=3000, C=6.0, class_weight="balanced")),
    ])
    model.fit(X_tr, y_tr)
    if verbose:
        pred = model.predict(X_te)
        print(f"[classifier] hold-out validation accuracy: {accuracy_score(y_te, pred):.3f}")
        print(classification_report(y_te, pred, zero_division=0))
    
    # Train final model on full dataset
    model.fit(X, y)
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    return model


def load_model():
    if os.path.exists(MODEL_PATH):
        try:
            return joblib.load(MODEL_PATH)
        except Exception as e:
            print(f"[classifier] Existing model could not be loaded ({e}), retraining...")
            return train()
    return train()


def prepare_document(article):
    """
    Creates a weighted textual representation giving high significance to the headline
    and opening lead sentence, preventing secondary historical background from dominating.
    """
    title = article.get("title", "").strip()
    text = article.get("text", "").strip()
    first_para = text.split("\n")[0] if "\n" in text else text[:300]
    # Headline repeated twice to weight topical intent over background mentions
    return f"{title}. {title}. {first_para} {text[:1500]}".strip()


def determine_subtype(label, text):
    """Assigns fine-grained event subtypes for enriched reporting and UI displays."""
    t_lower = text.lower()
    if label == "ACQUISITION":
        if "controlling stake" in t_lower or "majority stake" in t_lower:
            return "Controlling Stake Acquisition"
        elif "all-cash" in t_lower or "cash buyout" in t_lower:
            return "All-Cash Buyout"
        elif "completes" in t_lower or "completed" in t_lower:
            return "Completed Acquisition"
        return "Definitive Acquisition Agreement"
    elif label == "MERGER":
        if "all-stock" in t_lower:
            return "All-Stock Strategic Merger"
        elif "approved" in t_lower or "board" in t_lower:
            return "Board-Approved Merger"
        return "Corporate Merger of Equals"
    elif label == "DIVESTITURE":
        if "subsidiary" in t_lower or "unit" in t_lower:
            return "Subsidiary Unit Divestiture"
        elif "non-core" in t_lower:
            return "Non-Core Asset Sale"
        return "Asset Carve-out & Stake Sale"
    elif label == "HOSTILE_TAKEOVER":
        if "poison pill" in t_lower:
            return "Hostile Takeover Defense (Poison Pill)"
        elif "tender offer" in t_lower:
            return "Unsolicited Hostile Tender Offer"
        return "Contested Takeover Battle"
    elif label == "EXECUTIVE_CHANGE":
        if "appoint" in t_lower or "name" in t_lower:
            return "Executive Leadership Appointment"
        elif "resign" in t_lower or "step down" in t_lower or "retire" in t_lower:
            return "Executive Departure / Resignation"
        return "Board & Leadership Transition"
    elif label == "IPO":
        if "draft" in t_lower or "drhp" in t_lower:
            return "Draft Red Herring Prospectus (DRHP) Filing"
        elif "listing" in t_lower or "subscribed" in t_lower:
            return "Stock Exchange Listing & Public Bidding"
        return "Initial Public Offering (IPO)"
    return "Market / Operational Update"


def classify(articles, model=None):
    """
    Classifies articles and enriches each article dict with:
      - 'event_type': Target class label
      - 'event_subtype': Fine-grained corporate event subtype
      - 'confidence': Model probability score
      - 'is_corporate_event': Boolean indicator
    """
    model = model or load_model()
    docs = [prepare_document(a) for a in articles]
    probs = model.predict_proba(docs)
    classes = list(model.classes_)

    for art, doc, p in zip(articles, docs, probs):
        idx = p.argmax()
        label, conf = classes[idx], float(p[idx])
        title = art.get("title", "")
        
        # 1. Hostile takeover guard
        if label in ("ACQUISITION", "MERGER") and HOSTILE_RE.search(doc):
            label = "HOSTILE_TAKEOVER"
            conf = max(conf, 0.92)

        # 2. Contextual guard against false positives from routine earnings & macro news
        # If headline is clearly non-event and lacks any event trigger verb:
        if NO_EVENT_HEADLINE_RE.search(title) and not EVENT_TRIGGER_HEADLINE_RE.search(title):
            label = "NO_EVENT"
            conf = max(conf, 0.88)
        
        # Low confidence fallback
        if conf < 0.35 and label != "NO_EVENT":
            label = "NO_EVENT"

        art["event_type"] = label
        art["event_subtype"] = determine_subtype(label, doc)
        art["confidence"] = round(conf, 3)
        art["is_corporate_event"] = (label != "NO_EVENT")

    return articles
