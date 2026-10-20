"""
Corporate Event Miner - runs the full pipeline:
  (a) crawl  ->  (b) classify  ->  (c) extract event info  ->  (d) company/subsidiary tree

Usage:
  python main.py --mode sample          # offline demo with bundled articles
  python main.py --mode live            # crawl real RSS feeds (needs internet)
  python main.py --mode live --per-feed 5
"""
import argparse
import csv
import json
import os
import sys

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src import classifier, crawler, extractor
from src.company_tree import CompanyGraph

OUT = "output"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["sample", "live"], default="sample")
    ap.add_argument("--per-feed", type=int, default=10)
    ap.add_argument("--retrain", action="store_true", help="retrain classifier")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)

    # (a) crawl
    if args.mode == "live":
        articles = crawler.crawl(per_feed=args.per_feed)
    else:
        articles = crawler.load_sample()
    crawler.save_articles(articles, f"{OUT}/articles_raw.json")
    print(f"\n(a) {len(articles)} articles loaded")

    # (b) classify
    model = classifier.train() if args.retrain or not os.path.exists(classifier.MODEL_PATH) \
        else classifier.load_model()
    articles = classifier.classify(articles, model)
    n_events = sum(a["is_corporate_event"] for a in articles)
    print(f"(b) {n_events} of {len(articles)} articles classified as corporate events")
    for a in articles:
        print(f"    {a['event_type']:<17} {a['confidence']:.2f}  {a['title'][:70]}")

    # (c) extract
    events = extractor.extract_all(articles)
    with open(f"{OUT}/events.json", "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2, ensure_ascii=False)
    cols = ["event_type", "acquirer", "target", "seller", "buyer", "companies", "people",
            "deal_value", "event_date", "title", "source", "url", "confidence"]
    with open(f"{OUT}/events.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for e in events:
            row = dict(e)
            row["companies"] = "; ".join(c for c in e["companies"] if c)
            row["people"] = "; ".join(f"{p['name']} ({p['change']} {p['role'] or ''})".strip()
                                      for p in e["people"])
            w.writerow(row)
    print(f"\n(c) extracted {len(events)} events -> {OUT}/events.csv")
    for e in events:
        who = e["acquirer"] or e["seller"] or (e["companies"][0] if e["companies"] else None)
        print(f"    [{e['event_type']}] {who} -> {e['target'] or e['buyer'] or ''} "
              f"| value={e['deal_value']} | people={[p['name'] for p in e['people']]}")

    # (d) tree
    graph = CompanyGraph()
    graph.add_from_articles(articles, events)
    graph.save(OUT)
    print("\n(d) Company / subsidiary tree:\n")
    try:
        print(graph.to_text())
    except UnicodeEncodeError:
        print(graph.to_text(ascii_only=True))
    print(f"All outputs saved in ./{OUT}/")


if __name__ == "__main__":
    main()
