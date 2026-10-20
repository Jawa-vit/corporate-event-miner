# Corporate Event Miner
Web Text Classification + Information Extraction on financial news.

## Tasks covered
| Task | Module |
|------|--------|
| a) Crawl / download / extract financial news articles | `src/crawler.py` |
| b) Classify if an article is a Corporate Event (Acquire / Sell / Hostile Takeover / Merger / Executive Change / IPO) | `src/classifier.py` |
| c) Extract corporate event information | `src/extractor.py` |
| d) Tree of a company and its subsidiaries | `src/company_tree.py` |

## Setup
```
pip install -r requirements.txt
```

## Run
```
python main.py --mode sample      # offline demo (bundled sample articles)
python main.py --mode live        # crawl BBC, SEC, Economic Times, Moneycontrol, Livemint RSS
python main.py --mode live --per-feed 5 --retrain
```

## Output (`output/` folder)
- `articles_raw.json` - crawled articles
- `events.csv`, `events.json` - extracted events
- `company_tree.txt`, `company_tree.json`, `company_tree.png` - company -> subsidiary tree
- `event_classifier.joblib` - trained model

## Notes
- Training data (`data/training_data.csv`) is synthetic (template based). Add real labelled headlines to improve accuracy, then run with `--retrain`.
- Sample articles use fictional companies.
- RSS URLs can change; edit `FEEDS` in `src/crawler.py` if a feed returns nothing.
