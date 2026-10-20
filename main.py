"""
Corporate Event Miner - runs the full pipeline:
  (a) crawl  ->  (b) classify  ->  (c) extract event info  ->  (d) company/subsidiary tree  ->  (e) executive dashboard

Usage:
  python main.py --mode sample          # offline demo with bundled articles
  python main.py --mode live            # crawl real RSS feeds (needs internet)
  python main.py --mode live --per-feed 5
  python main.py --mode sample --retrain
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

from src import classifier, crawler, extractor, dashboard
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
    print(f"\n=======================================================")
    print(f"(a) CRAWL: {len(articles)} articles ingested")
    print(f"=======================================================")

    # (b) classify
    model = classifier.train() if args.retrain or not os.path.exists(classifier.MODEL_PATH) \
        else classifier.load_model()
    articles = classifier.classify(articles, model)
    n_events = sum(a["is_corporate_event"] for a in articles)
    print(f"\n=======================================================")
    print(f"(b) CLASSIFY: {n_events} of {len(articles)} articles classified as corporate events")
    print(f"=======================================================")
    for a in articles:
        flag = "[EVENT]" if a["is_corporate_event"] else "[NO-EV]"
        print(f"    {flag} {a['event_type']:<17} (conf: {a['confidence']:.2f}) | {a['title'][:65]}")

    # (c) extract
    events = extractor.extract_all(articles)
    with open(f"{OUT}/events.json", "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2, ensure_ascii=False)
    
    cols = [
        "event_type", "event_subtype", "acquirer", "target", "seller", "buyer",
        "deal_value", "deal_structure", "event_date", "effective_timeline", "status",
        "event_brief", "companies", "people", "title", "source", "url", "confidence"
    ]

    target_csv = f"{OUT}/events.csv"
    try:
        with open(target_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            for e in events:
                row = dict(e)
                row["companies"] = "; ".join(c for c in e.get("companies", []) if c)
                row["people"] = "; ".join(f"{p['name']} ({p['change']} {p['role'] or ''})".strip()
                                          for p in e.get("people", []))
                w.writerow(row)
    except PermissionError:
        alt_csv = f"{OUT}/events_latest.csv"
        print(f"   [!] Note: {target_csv} is currently locked by another application (e.g., WPS/Excel).")
        print(f"       Saving updated table to {alt_csv} instead.")
        with open(alt_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            for e in events:
                row = dict(e)
                row["companies"] = "; ".join(c for c in e.get("companies", []) if c)
                row["people"] = "; ".join(f"{p['name']} ({p['change']} {p['role'] or ''})".strip()
                                          for p in e.get("people", []))
                w.writerow(row)
        target_csv = alt_csv
    
    print(f"\n=======================================================")
    print(f"(c) EXTRACT: {len(events)} structured events extracted -> {target_csv}")
    print(f"=======================================================")
    for e in events:
        who = e["acquirer"] or e["seller"] or (e["companies"][0] if e["companies"] else "N/A")
        tgt = e["target"] or e["buyer"] or ""
        flow = f"{who} -> {tgt}" if tgt else who
        print(f"\n  • [{e['event_type']}: {e['event_subtype']}]")
        print(f"    Parties   : {flow}")
        print(f"    Terms     : {e['deal_value'] or 'N/A'} ({e['deal_structure']})")
        print(f"    Timeline  : Date: {e['event_date']} | Status: {e['status']} | Expected: {e['effective_timeline']}")
        print(f"    Brief     : {e['event_brief']}")

    # (d) tree
    graph = CompanyGraph()
    graph.add_from_articles(articles, events)
    graph.save(OUT)
    print(f"\n=======================================================")
    print(f"(d) TREE: Company / subsidiary hierarchy generated")
    print(f"=======================================================")
    try:
        print(graph.to_text())
    except UnicodeEncodeError:
        print(graph.to_text(ascii_only=True))

    # (e) dashboard
    dash_path = dashboard.generate(articles, events, graph, f"{OUT}/dashboard.html")
    print(f"=======================================================")
    print(f"(e) DASHBOARD: Interactive presentation dashboard built")
    print(f"    👉 file:///{os.path.abspath(dash_path).replace(os.sep, '/')}")
    print(f"=======================================================")
    print(f"\nAll outputs successfully saved to ./{OUT}/")


if __name__ == "__main__":
    main()
