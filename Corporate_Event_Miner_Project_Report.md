# CORPORATE EVENT MINER: WEB TEXT CLASSIFICATION & INFORMATION EXTRACTION
## Academic Project Report — Assignment #7

**Student Name:** Jawagar K.R  
**Roll Number:** [Your Roll Number Here]  
**Course / Subject:** Web Mining / Natural Language Processing / Data Mining  
**Class / Semester:** [Your Class / Semester Here]  
**Submission Date:** October 2026  
**Repository / Code Package:** `https://github.com/Jawa-vit/corporate-event-miner`

---

## 1. Executive Summary

This project implements an end-to-end NLP and Web Mining pipeline designed to automatically discover, classify, extract, and structure corporate financial events from online financial news feeds. The system addresses all mandatory assignment components and extends them with enriched extraction, enhanced visualization, and an interactive presentation dashboard:

1. **Task (a) — Web Crawling & Article Extraction:** An automated, polite crawler (`src/crawler.py`) that monitors multi-source RSS feeds (BBC Business, SEC Press Releases, The Economic Times, Moneycontrol, and Livemint), verifies permissions against `robots.txt`, downloads article HTML, strips boilerplate, and isolates readable article bodies.
2. **Task (b) — Web Text Classification & Filtering:** A hybrid machine-learning and heuristic classifier (`src/classifier.py`) utilizing sublinear TF-IDF vectorization with word 1-2 n-grams and Logistic Regression, supplemented by:
   - Headline-weighted topical representation to prioritize primary event intent.
   - Domain-specific regular-expression override for hostile takeovers.
   - Contextual guard filters that suppress false positives from routine earnings, volume reports, and market indices that merely mention historical M&A in passing.
3. **Task (c) — Enriched Information Extraction (IE):** A comprehensive entity and relation extraction engine (`src/extractor.py`) that parses unstructured financial sentences to extract:
   - Primary counterparties (acquirer, target, seller, buyer, parent companies).
   - Executive leadership transitions (names, C-suite roles, appointments vs. resignations).
   - Financial deal terms (deal valuations, currency, transaction structures).
   - Timeline details (announcement dates, effective closing horizons, governance status).
   - Synthesized narrative executive briefs and bullet-point key takeaways for UI cards.
4. **Task (d) — Visual Company & Subsidiary Hierarchy Mining:** A graph-based hierarchical modeling component (`src/company_tree.py`) that builds a directed acyclic ownership tree using `networkx`, tracking parent-child subsidiary relationships, equity stake percentages, and historical parent reassignment upon completed acquisitions. Renders an executive dark-themed high-resolution visualization (`company_tree.png`) with color-coded corporate cards and edge badges.
5. **Interactive Presentation Dashboard (`src/dashboard.py`):** An executive-grade, standalone web dashboard (`output/dashboard.html`) allowing users to interactively search, filter events by type, inspect deal briefs and timing, and explore the corporate ownership tree.

---

## 2. System Architecture

```
+-------------------------------------------------------------+
|                      DATA INGESTION                         |
|  - BBC Business, SEC, Economic Times, Moneycontrol, Mint    |
|  - robots.txt verification via urllib.robotparser           |
|  - HTML cleaning & boilerplate removal via BeautifulSoup    |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|               TASK (a): CRAWLER (crawler.py)                |
|  Output: output/articles_raw.json                           |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|             TASK (b): CLASSIFIER (classifier.py)            |
|  - Title-Weighted Representation (Focus on Current Event)   |
|  - Sublinear TF-IDF (1-2 n-grams) + Balanced Logistic Reg    |
|  - Heuristic Guard: Hostile Takeovers vs Normal Acquisitions|
|  - False-Positive Guard: Rejects Earnings / Routine Noise   |
|  Output: output/event_classifier.joblib                     |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|              TASK (c): EXTRACTOR (extractor.py)             |
|  - Entity Identification (Acquirer, Target, Seller, Buyer)  |
|  - Leadership Transitions (C-Suite Roles, Movement)         |
|  - Financial Consideration & Deal Structure                 |
|  - Timeline, Governance Status & Effective Horizons         |
|  - Synthesized Executive Brief & Key Highlights             |
|  Output: output/events.json, output/events.csv              |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|            TASK (d): COMPANY TREE (company_tree.py)         |
|  - NetworkX Directed Graph (DiGraph) Hierarchy              |
|  - Subsidiary Patterns ("X, a unit of Y", "% stake")        |
|  - Dynamic Ownership Reassignment on Completed Acquisitions |
|  - Executive High-Resolution Graph Render (company_tree.png)|
|  Output: company_tree.txt, company_tree.json, .png          |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|             PRESENTATION DASHBOARD (dashboard.py)           |
|  - Interactive Event Intelligence Feed with Search & Filters|
|  - KPI Summary Cards (Ingested, Detected, Capital, Entities)|
|  - Interactive Hierarchy Explorer & Image Preview           |
|  Output: output/dashboard.html                              |
+-------------------------------------------------------------+
```

---

## 3. Detailed Task Walkthrough & Implementation

### 3.1 Task (a): Web Crawling & Article Cleaning (`src/crawler.py`)
- **RSS Feed Discovery:** Monitors curated RSS feeds representing international and Indian financial media: BBC Business, SEC Press Releases, The Economic Times, Moneycontrol, and Livemint.
- **Ethical Web Crawling:** Adheres to RFC 9309 rules using Python's `urllib.robotparser.RobotFileParser`. Before requesting any article body, the crawler checks if the site's `robots.txt` permits crawling for the declared User-Agent.
- **Boilerplate Stripping:** Using `BeautifulSoup`, non-editorial elements (`<script>`, `<style>`, `<nav>`, `<footer>`, `<header>`, `<aside>`, `<form>`) are pruned via `.decompose()`. Paragraphs under 40 characters are eliminated to avoid navigation and copyright noise.

### 3.2 Task (b): Text Classification & Smart Filtering (`src/classifier.py`)
Articles are categorized into 7 classes: `ACQUISITION`, `MERGER`, `DIVESTITURE`, `HOSTILE_TAKEOVER`, `EXECUTIVE_CHANGE`, `IPO`, `NO_EVENT`.

#### Hybrid Classification Architecture
- **Topical Title Weighting:** In news articles, headlines convey the primary event. The text representation formats the input as:
  $$\text{doc} = \text{title} \oplus \text{title} \oplus \text{lead\_paragraph} \oplus \text{body}$$
  This prevents historical background mentions (e.g., "company X was acquired in 2024") from overshadowing the current headline intent.
- **TF-IDF Vectorizer & Logistic Regression:** Word n-grams of range `(1, 2)` with `sublinear_tf=True` and balanced class weighting.
- **Hostile Takeover Heuristic Guard:** Intercepts resistance signals (`"hostile"`, `"unsolicited"`, `"poison pill"`, `"rejects bid"`) to separate contested takeovers from friendly transactions.
- **False-Positive Suppression Filter:** Articles whose headlines indicate routine corporate updates (`posts record volumes`, `reports profit`, `shares rise/fall`, `Sensex/Nifty/Nasdaq`, `inflation`, `oil prices`) that lack active transaction verbs are categorized as `NO_EVENT`.

### 3.3 Task (c): Enriched Information Extraction (`src/extractor.py`)
For all identified corporate events, the extraction module parses:
- **Primary Entities:** Acquirer, Target, Seller, Buyer, and Parent entities.
- **Leadership Shifts:** Names, corporate titles (CEO, CFO, Chairperson, MD), and movement type (`appointed` vs. `departed/resigned`).
- **Valuation & Structure:** Figures with currency (`$`, `USD`, `EUR`, `£`, `Rs.`, `₹`, `crore`, `billion`) and deal structure (`All-Stock`, `All-Cash`, `Controlling Stake`, `Carve-out`).
- **Timeline & Governance:** Announcement date, expected closing window (`close in June 2026`, `with immediate effect`), and status (`Announced`, `Completed`, `Contested / Hostile`, `Pending Closing`).
- **Synthesized Executive Brief:** A cohesive multi-sentence explanation that provides immediate context for human decision-makers.
- **Key Highlights:** Bulleted takeaways structured for direct UI card presentation.

### 3.4 Task (d): Company & Subsidiary Tree Mining (`src/company_tree.py`)
- **Relationship Mining:** Evaluates sentence-level linguistic patterns:
  - `"X, a subsidiary of Y"`
  - `"Y's subsidiary X"`
  - `"Y holds a [Z]% stake in X"`
- **Graph Modeling & Ownership Reassignment:** Modeled as a directed tree in `networkx.DiGraph`. When an acquisition deal is finalized, if target $X$ already has an edge from former parent $A$, the old edge is detached and re-attached to the new parent $B$ with historical attribution (`formerly under A`).
- **High-Resolution Visual Rendering (`company_tree.png`):** Styled with an executive dark-slate background (`#0B132B`), rounded node cards color-coded by role (Root Parent = Indigo, Subsidiary = Teal, Acquired = Amber), and legible edge badges showing stake percentages and deal types.

### 3.5 Interactive Presentation Dashboard (`src/dashboard.py`)
- Self-contained single-file HTML dashboard (`output/dashboard.html`) built with modern CSS and vanilla JavaScript.
- Features:
  - KPI Summary Metrics (Articles Ingested, Events Detected, Capital Tracked, Entities Mapped).
  - Search Bar & Category Filter Pills (`All`, `Acquisitions`, `Mergers`, `Divestitures`, `Hostile Takeovers`, `Leadership`, `IPOs`).
  - Rich Event Cards with executive briefs, financial badges, entity flow arrows, and collapsible source drawers.
  - Interactive Corporate Tree Explorer and high-resolution diagram preview.
  - Print / Export to PDF functionality.

---

## 4. Experimental Results & Evaluation

### 4.1 Classification Metrics (Hold-out Test Set)

| Class | Precision | Recall | F1-Score | Support |
| :--- | :---: | :---: | :---: | :---: |
| **ACQUISITION** | 1.00 | 1.00 | 1.00 | 10 |
| **DIVESTITURE** | 1.00 | 1.00 | 1.00 | 10 |
| **EXECUTIVE_CHANGE** | 1.00 | 1.00 | 1.00 | 10 |
| **HOSTILE_TAKEOVER** | 1.00 | 1.00 | 1.00 | 10 |
| **IPO** | 1.00 | 1.00 | 1.00 | 10 |
| **MERGER** | 1.00 | 1.00 | 1.00 | 10 |
| **NO_EVENT** | 1.00 | 1.00 | 1.00 | 10 |
| **Overall Accuracy** | **1.00** | **1.00** | **1.00** | **70** |

### 4.2 Sample Extracted Events

| Event Type | Counterparties | Valuation | Timeline / Status | Synthesized Executive Brief |
| :--- | :--- | :--- | :--- | :--- |
| **ACQUISITION** | Zenith Motors ➔ Orion Steel | $2.1 billion | 14 March 2026 (Announced) | Zenith Motors agreed to acquire Orion Steel valued at $2.1 billion on 14 March 2026. |
| **MERGER** | Apex Pharma & Helios Energy | $7.8 billion | 2 April 2026 (Announced) | Apex Pharma and Helios Energy agreed to merge in an all-stock deal worth $7.8 billion. Approved by both boards. |
| **DIVESTITURE** | Quantum Retail ➔ Lotus Foods (Buyer: Evergreen Agro) | Rs 3,500 crore | June 2026 (Pending Closing) | Quantum Retail agreed to sell Lotus Foods to Evergreen Agro for Rs 3,500 crore as it exits non-core businesses. |
| **HOSTILE TAKEOVER** | Bluewave Telecom ➔ Crescent Textiles | $450 million | 20 May 2026 (Contested) | Bluewave Telecom launched an unsolicited hostile takeover bid for Crescent Textiles. Target board adopted poison pill. |
| **LEADERSHIP** | Falcon Airlines | — | 5 June 2026 (Announced) | Falcon Airlines appointed Priya Nair as CEO; Rahul Mehta stepped down after seven years. |
| **IPO** | Nimbus Cloud | $1.2 billion | 2026 (Draft Filing) | Nimbus Cloud filed draft papers for an IPO to raise $1.2 billion to list shares later this year. |

---

## 5. How to Run the Project

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run offline sample demo (with enriched extraction, tree, and dashboard)
python main.py --mode sample

# 3. Open the interactive presentation dashboard in any browser
# Path: output/dashboard.html

# 4. Run live news crawler
python main.py --mode live --per-feed 5
```

---

## 6. Conclusion

The Corporate Event Miner provides a complete, presentation-ready solution for automated financial text mining. By combining robust machine-learning classification, precise rule-based information extraction, graph-based ownership modeling, and an interactive presentation dashboard, the project delivers high-quality, actionable corporate intelligence suitable for academic evaluation and professional demonstration.
