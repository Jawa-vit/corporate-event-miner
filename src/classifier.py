"""
Task (b): Classify whether an article is about a Corporate Event.

Hybrid approach:
  1. TF-IDF (word 1-2 grams) + Logistic Regression  -> machine-learning classifier
  2. Keyword rule for hostile takeovers              -> fixes the hardest class
     (hostile bids look like normal acquisitions to a bag-of-words model)
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

HOSTILE_RE = re.compile(
    r"hostile|unsolicited|poison pill|rejects? (?:the )?(?:bid|offer)|"
    r"fend(?:s|ing)? off|resist(?:s|ing)? the (?:bid|offer)|tender offer directly", re.I)


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
        ("clf", LogisticRegression(max_iter=2000, C=5.0)),
    ])
    model.fit(X_tr, y_tr)
    if verbose:
        pred = model.predict(X_te)
        print(f"[classifier] hold-out accuracy: {accuracy_score(y_te, pred):.3f}")
        print(classification_report(y_te, pred, zero_division=0))
    model.fit(X, y)  # final model uses all data
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


def classify(articles, model=None):
    """Adds 'event_type' and 'confidence' to each article dict."""
    model = model or load_model()
    docs = [(a["title"] + ". " + a["text"])[:2000] for a in articles]
    probs = model.predict_proba(docs)
    classes = list(model.classes_)
    for art, doc, p in zip(articles, docs, probs):
        idx = p.argmax()
        label, conf = classes[idx], float(p[idx])
        if label in ("ACQUISITION", "MERGER") and HOSTILE_RE.search(doc):
            label = "HOSTILE_TAKEOVER"
        art["event_type"] = label
        art["confidence"] = round(conf, 3)
        art["is_corporate_event"] = label != "NO_EVENT"
    return articles
