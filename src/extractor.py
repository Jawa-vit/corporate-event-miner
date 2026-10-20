"""
Task (c): Extract Corporate Event information.

Uses regular-expression patterns (rule-based information extraction) to pull out:
  event type, companies involved (acquirer / target / seller / buyer),
  deal value, dates, people + roles (for executive changes), and a one-line summary.
"""
import re

CAP = r"[A-Z][A-Za-z0-9&'\-]*"
COMPANY = rf"{CAP}(?:\s+{CAP})*(?:\s+(?:of|&)\s+{CAP}(?:\s+{CAP})*)?"
PERSON = rf"(?:(?:Dr|Mr|Ms|Mrs|Shri|Smt)\.?\s+)?{CAP}(?:\s+{CAP}){{1,2}}"
ROLE = (r"(?:[A-Za-z\-]+\s+){0,3}?"
        r"(?:CEO|CFO|COO|CTO|Chairman|Chairperson|Chair|President|Managing Director|Director|Officer)")
VALUE = (r"(?:Rs\.?|INR|₹|US\$|\$|USD|EUR|€|£)\s?\d[\d,]*(?:\.\d+)?"
         r"(?:\s?(?:billion|million|trillion|lakh crore|crore|bn|mn|cr))?")
DATE = (r"(?:\d{1,2}\s)?(?:January|February|March|April|May|June|July|August|September|"
        r"October|November|December)\s(?:\d{1,2},?\s)?\d{4}")

LEAD_STOP = {"Today", "Yesterday", "The", "On", "In", "Monday", "Tuesday", "Wednesday", "Thursday",
             "Friday", "Saturday", "Sunday", "Shares", "Rival", "Its", "This", "That", "After",
             "Mumbai", "Delhi", "London", "New", "Reuters", "According"}
LEAD_STOP.discard("New")  # "New Horizon Ltd" is a valid company name

_TAIL = r"\.?,?\s+(?:has\s+|have\s+|will\s+|had\s+|is\s+set\s+to\s+|agreed\s+to\s+|plans\s+to\s+|to\s+)*"

ACQ_ACTIVE = re.compile(
    rf"(?P<acq>{COMPANY}){_TAIL}(?:acquire[sd]?|buy|buys|bought|snaps?\s+up|take[s]?\s+over|"
    rf"completes\s+(?:the\s+)?acquisition\s+of|launch(?:es|ed)?\s+(?:a\s+)?hostile\s+(?:takeover\s+)?(?:bid|offer)\s+for|"
    rf"makes\s+(?:an\s+)?(?:unsolicited|hostile)\s+(?:takeover\s+)?(?:bid|offer|approach)\s+for)\s+"
    rf"(?:rival\s+|a\s+controlling\s+stake\s+in\s+)?(?P<tgt>{COMPANY})")
ACQ_PASSIVE = re.compile(
    rf"(?P<tgt>{COMPANY})\s+(?:was|is|has\s+been|will\s+be)\s+acquired\s+by\s+(?P<acq>{COMPANY})")
HOSTILE_REJECT = re.compile(
    rf"(?P<tgt>{COMPANY})(?:'s\s+board)?\s+(?:board\s+)?rejects?\s+(?:an?\s+)?(?:the\s+)?unsolicited\s+(?:{VALUE}\s+)?"
    rf"(?:offer|bid)\s+from\s+(?P<acq>{COMPANY})")
MERGE = [
    re.compile(rf"(?P<a>{COMPANY})\s+and\s+(?P<b>{COMPANY})\s+(?:have\s+|will\s+|to\s+|agreed?\s+to\s+)+merge"),
    re.compile(rf"(?P<a>{COMPANY}){_TAIL}merge[sd]?\s+with\s+(?P<b>{COMPANY})"),
    re.compile(rf"merger\s+(?:of|between)\s+(?P<a>{COMPANY})\s+and\s+(?P<b>{COMPANY})"),
]
SELL = [
    re.compile(rf"(?P<seller>{COMPANY}){_TAIL}(?:sell|sells|sold|divest|divests|divested|offloads?)\s+"
               rf"(?:its\s+|the\s+|a\s+)?(?:stake\s+in\s+|entire\s+stake\s+in\s+|subsidiary\s+)?(?P<asset>{COMPANY})"),
    re.compile(rf"(?P<seller>{COMPANY}){_TAIL}completes\s+(?:the\s+)?sale\s+of\s+(?P<asset>{COMPANY})"),
]
BUYER = re.compile(rf"(?:sell|sells|sold|sale)[^.]*?\sto\s+(?P<buyer>{COMPANY})")
APPOINT = re.compile(
    rf"(?P<company>{COMPANY})\s+(?:has\s+)?(?:appoint(?:s|ed)|name(?:s|d)|elect(?:s|ed)|promote(?:s|d))\s+"
    rf"(?P<person>{PERSON})\s+(?:as\s+)?(?:its\s+|the\s+|new\s+)*(?P<role>{ROLE})")
RESIGN = re.compile(
    rf"(?P<person>{PERSON})\s+(?:has\s+)?(?:resign(?:s|ed)|step(?:s|ped)\s+down|quit|quits|retire[sd]?)"
    rf"(?:\s+as\s+(?P<role>{ROLE}))?(?:\s+(?:of|at|from)\s+(?P<company>{COMPANY}))?")
IPO_RE = re.compile(rf"(?P<company>{COMPANY})\s+(?:files|launches|sets|plans|gets|announces)[^.]*?(?:IPO|initial public offering|public issue)")

VALUE_RE = re.compile(VALUE)
DATE_RE = re.compile(DATE)
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'])")


def clean_company(name):
    """Strip leading filler words and trailing punctuation from a company candidate."""
    if not name:
        return None
    words = name.strip(" ,.;:").split()
    while words and words[0] in LEAD_STOP:
        words.pop(0)
    out = " ".join(words)
    return out if len(out) > 2 else None


def canonical(name):
    """Key used to treat 'Apex Pharma Inc' and 'Apex Pharma' as the same company."""
    key = re.sub(r"\b(ltd|limited|inc|corp|corporation|plc|co|llc)\b\.?", "", name.lower())
    return re.sub(r"[^a-z0-9 ]", "", key).strip()


def sentences(text):
    return [s.strip() for s in SENT_SPLIT.split(text.replace("\n", " ")) if s.strip()]


def extract_event(article):
    """Returns a dict with structured information for one classified article."""
    etype = article.get("event_type", "NO_EVENT")
    text = (article["title"] + ". " + article["text"]).strip()
    info = {
        "event_type": etype, "acquirer": None, "target": None, "seller": None, "buyer": None,
        "companies": [], "people": [], "deal_value": None, "event_date": None,
    }
    sents = sentences(text)

    def first(pattern_list, key_map):
        pats = pattern_list if isinstance(pattern_list, list) else [pattern_list]
        for s in sents:
            for p in pats:
                m = p.search(s)
                if m:
                    return m, s
        return None, None

    if etype in ("ACQUISITION", "HOSTILE_TAKEOVER"):
        m, s = first([HOSTILE_REJECT, ACQ_ACTIVE, ACQ_PASSIVE], None)
        if m:
            info["acquirer"], info["target"] = clean_company(m["acq"]), clean_company(m["tgt"])
    elif etype == "MERGER":
        m, s = first(MERGE, None)
        if m:
            info["companies"] = [c for c in (clean_company(m["a"]), clean_company(m["b"])) if c]
    elif etype == "DIVESTITURE":
        m, s = first(SELL, None)
        if m:
            info["seller"], info["target"] = clean_company(m["seller"]), clean_company(m["asset"])
            for s2 in sents:                      # buyer may be named in a later sentence
                b = BUYER.search(s2)
                if b and (info["target"] or "") in s2:
                    info["buyer"] = clean_company(b["buyer"])
                    break
    elif etype == "EXECUTIVE_CHANGE":
        seen = set()
        for s in sents:
            for kind, pat in (("appointed", APPOINT), ("departed", RESIGN)):
                for m in pat.finditer(s):
                    d = m.groupdict()
                    key = (d["person"], kind)
                    if key in seen:
                        continue
                    seen.add(key)
                    info["people"].append({
                        "name": d["person"], "role": (d.get("role") or "").strip() or None,
                        "company": clean_company(d.get("company")), "change": kind})
        if info["people"]:
            info["companies"] = [info["people"][0]["company"]] if info["people"][0]["company"] else []
    elif etype == "IPO":
        m, _ = first(IPO_RE, None)
        if m:
            info["companies"] = [clean_company(m["company"])]

    # Generic fields
    v = VALUE_RE.search(text)
    info["deal_value"] = v.group(0).strip() if v else None
    d = DATE_RE.search(text)
    info["event_date"] = d.group(0) if d else article.get("published") or None
    info["summary"] = sents[0] if sents else article["title"]
    return info


def extract_all(articles):
    events = []
    for a in articles:
        if not a.get("is_corporate_event"):
            continue
        info = extract_event(a)
        info.update({"title": a["title"], "source": a["source"], "url": a["url"],
                     "confidence": a["confidence"]})
        events.append(info)
    return events
