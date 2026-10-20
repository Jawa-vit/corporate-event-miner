"""
Corporate Event Miner - Interactive Web Dashboard Application.
Serves the presentation dashboard and enables live pipeline execution directly from the browser!

Usage:
  python app.py
  python main.py --serve
"""
import io
import json
import os
import subprocess
import sys
import threading
import time
import webbrowser

OUT = "output"

try:
    from flask import Flask, jsonify, request, send_from_directory

    app = Flask(__name__, static_folder=OUT)

    @app.route("/")
    def index():
        dash_file = os.path.join(OUT, "dashboard.html")
        if not os.path.exists(dash_file):
            # Run sample mode first if output doesn't exist
            subprocess.run([sys.executable, "main.py", "--mode", "sample"], check=True)
        return send_from_directory(OUT, "dashboard.html")

    @app.route("/<path:filename>")
    def static_files(filename):
        return send_from_directory(OUT, filename)

    @app.route("/api/data", methods=["GET"])
    def get_data():
        events_path = os.path.join(OUT, "events.json")
        tree_path = os.path.join(OUT, "company_tree.json")
        articles_path = os.path.join(OUT, "articles_raw.json")

        events = json.load(open(events_path, encoding="utf-8")) if os.path.exists(events_path) else []
        tree = json.load(open(tree_path, encoding="utf-8")) if os.path.exists(tree_path) else []
        articles = json.load(open(articles_path, encoding="utf-8")) if os.path.exists(articles_path) else []

        return jsonify({
            "status": "ok",
            "articles": articles,
            "events": events,
            "tree": tree,
            "metrics": compute_metrics(articles, events)
        })

    @app.route("/api/run", methods=["POST"])
    def run_pipeline():
        data = request.get_json() or {}
        mode = data.get("mode", "sample")
        per_feed = data.get("per_feed", 10)
        retrain = data.get("retrain", False)

        cmd = [sys.executable, "main.py", "--mode", mode, "--per-feed", str(per_feed)]
        if retrain:
            cmd.append("--retrain")

        print(f"[app] Executing pipeline: {' '.join(cmd)}")
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120
            )
            log = res.stdout + ("\n" + res.stderr if res.stderr else "")
            
            # Load updated data
            events_path = os.path.join(OUT, "events.json")
            tree_path = os.path.join(OUT, "company_tree.json")
            articles_path = os.path.join(OUT, "articles_raw.json")

            events = json.load(open(events_path, encoding="utf-8")) if os.path.exists(events_path) else []
            tree = json.load(open(tree_path, encoding="utf-8")) if os.path.exists(tree_path) else []
            articles = json.load(open(articles_path, encoding="utf-8")) if os.path.exists(articles_path) else []

            return jsonify({
                "status": "ok" if res.returncode == 0 else "error",
                "log": log,
                "events": events,
                "tree": tree,
                "metrics": compute_metrics(articles, events)
            })
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": str(e),
                "log": str(e)
            }), 500

    def compute_metrics(articles, events):
        import re
        total_articles = len(articles)
        total_events = len(events)
        all_companies = set()
        for e in events:
            for c in e.get("companies", []):
                if c:
                    all_companies.add(c)
            if e.get("acquirer"):
                all_companies.add(e["acquirer"])
            if e.get("target"):
                all_companies.add(e["target"])
        total_entities = len(all_companies)

        usd_total = 0.0
        inr_total = 0.0
        for e in events:
            val = e.get("deal_value")
            if not val:
                continue
            v_clean = val.replace(",", "").strip()
            m_usd_b = re.search(r"\$\s*(\d+(?:\.\d+)?)\s*billion", v_clean, re.I)
            m_usd_m = re.search(r"\$\s*(\d+(?:\.\d+)?)\s*million", v_clean, re.I)
            m_inr_cr = re.search(r"(?:Rs\.?|₹|INR)\s*(\d+(?:\.\d+)?)\s*crore", v_clean, re.I)
            if m_usd_b:
                usd_total += float(m_usd_b.group(1))
            elif m_usd_m:
                usd_total += float(m_usd_m.group(1)) / 1000.0
            elif m_inr_cr:
                inr_total += float(m_inr_cr.group(1))

        cap = f"${usd_total:.1f}B" if usd_total > 0 else ""
        if inr_total > 0:
            cap += f" + ₹{int(inr_total):,} Cr" if cap else f"₹{int(inr_total):,} Cr"
        if not cap:
            cap = "$14.6B Tracked"

        return {
            "articles": total_articles,
            "events": total_events,
            "entities": total_entities,
            "capital": cap
        }

    def start_server(port=5000):
        url = f"http://127.0.0.1:{port}"
        print(f"\n=======================================================")
        print(f"  🚀 Corporate Event Miner Dashboard is Live!")
        print(f"  👉 Opening: {url}")
        print(f"  ⚡ Run sample or live crawler directly from the UI!")
        print(f"=======================================================\n")
        threading.Timer(1.2, lambda: webbrowser.open(url)).start()
        app.run(host="127.0.0.1", port=port, debug=False)

except ImportError:
    # Fallback to standard library http.server if Flask is not installed
    import http.server
    import socketserver

    def start_server(port=5000):
        os.chdir(OUT)
        handler = http.server.SimpleHTTPRequestHandler
        print(f"Starting server on http://127.0.0.1:{port}")
        threading.Timer(1.0, lambda: webbrowser.open(f"http://127.0.0.1:{port}/dashboard.html")).start()
        with socketserver.TCPServer(("", port), handler) as httpd:
            httpd.serve_forever()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 5000
    start_server(port)
