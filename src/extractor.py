"""
Task (c): Extract Detailed Corporate Event Information.

Extracts structured, presentation-ready intelligence from financial news articles:
  - Event type and fine-grained subtype
  - Primary entities (Acquirer, Target, Seller, Buyer, Parent Company)
  - Executive Leadership details (incoming/outgoing, C-suite roles, tenure)
  - Financials (valuation, currency, transaction structure)
  - Timing & Milestones (announcement date, expected closing, effective timing)
  - Narrative Executive Brief (synthesized multi-sentence explanation)
  - Bullet-point Highlights (tailored for direct UI card display)
"""
import re

CAP = r"[A-Z][A-Za-z0-9&'\-]*"
COMPANY = rf"{CAP}(?:\s+{CAP})*(?:\s+(?:of|&)\s+{CAP}(?:\s+{CAP})*)?"
PERSON = rf"(?:(?:Dr|Mr|Ms|Mrs|Shri|Smt)\.?\s+)?{CAP}(?:\s+{CAP}){{1,2}}"
ROLE = (r"(?:[A-Za-z\-]+\s+){0,3}?"
        r"(?:CEO|CFO|COO|CTO|Chief Executive Officer|Chief Financial Officer|"
        r"Chief Operating Officer|Chief Technology Officer|Chairman|Chairperson|"
        r"Chair|President|Managing Director|Director|Officer)")

VALUE = (r"(?:Rs\.?|INR|₹|US\$|\$|USD|EUR|€|£)\s?\d[\d,]*(?:\.\d+)?"
         r"(?:\s?(?:billion|million|trillion|lakh crore|crore|bn|mn|cr))?")

DATE = (r"(?:\d{1,2}\s)?(?:January|February|March|April|May|June|July|August|September|"
        r"October|November|December)\s(?:\d{1,2},?\s)?\d{4}")

FUTURE_TIMELINE = (
    r"(?:close(?:s)?\s+in\s+[A-Za-z]+\s+\d{4}|"
    r"later\s+this\s+year|next\s+month|with\s+immediate\s+effect|"
    r"by\s+(?:end\s+of\s+)?(?:Q[1-4]\s+)?\d{4}|effective\s+[A-Za-z]+\s+\d{4})"
)

LEAD_STOP = {"Today", "Yesterday", "The", "On", "In", "Monday", "Tuesday", "Wednesday", "Thursday",
             "Friday", "Saturday", "Sunday", "Shares", "Rival", "Its", "This", "That", "After",
             "Mumbai", "Delhi", "London", "Reuters", "According"}

_TAIL = r"\.?,?\s+(?:has\s+|have\s+|will\s+|had\s+|is\s+set\s+to\s+|agreed\s+to\s+|plans\s+to\s+|to\s+)*"

ACQ_ACTIVE = re.compile(
    rf"(?P<acq>{COMPANY}){_TAIL}(?:acquire[sd]?|buy|buys|bought|snaps?\s+up|take[s]?\s+over|"
    rf"completes\s+(?:the\s+)?acquisition\s+of|launch(?:es|ed)?\s+(?:a\s+)?hostile\s+(?:takeover\s+)?(?:bid|offer)\s+for|"
    rf"makes\s+(?:an\s+)?(?:unsolicited|hostile)\s+(?:takeover\s+)?(?:bid|offer|approach)\s+for)\s+"
    rf"(?:rival\s+|a\s+controlling\s+stake\s+in\s+)?(?P<tgt>{COMPANY})"
)
ACQ_PASSIVE = re.compile(
    rf"(?P<tgt>{COMPANY})\s+(?:was|is|has\s+been|will\s+be)\s+acquired\s+by\s+(?P<acq>{COMPANY})"
)
HOSTILE_REJECT = re.compile(
    rf"(?P<tgt>{COMPANY})(?:'s\s+board)?\s+(?:board\s+)?rejects?\s+(?:an?\s+)?(?:the\s+)?unsolicited\s+(?:{VALUE}\s+)?"
    rf"(?:offer|bid)\s+from\s+(?P<acq>{COMPANY})"
)
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
    rf"(?P<person>{PERSON})\s+(?:as\s+)?(?:its\s+|the\s+|new\s+)*(?P<role>{ROLE})"
)
RESIGN = re.compile(
    rf"(?P<person>{PERSON})\s+(?:has\s+)?(?:resign(?:s|ed)|step(?:s|ped)\s+down|quit|quits|retire[sd]?)"
    rf"(?:\s+as\s+(?P<role>{ROLE}))?(?:\s+(?:of|at|from)\s+(?P<company>{COMPANY}))?"
)
IPO_RE = re.compile(
    rf"(?P<company>{COMPANY})\s+(?:files|launches|sets|plans|gets|announces)[^.]*?(?:IPO|initial public offering|public issue|DRHP)"
)

VALUE_RE = re.compile(VALUE)
DATE_RE = re.compile(DATE)
TIMELINE_RE = re.compile(FUTURE_TIMELINE, re.I)
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'])")


def clean_company(name):
    if not name:
        return None
    words = name.strip(" ,.;:").split()
    while words and words[0] in LEAD_STOP:
        words.pop(0)
    out = " ".join(words)
    return out if len(out) > 2 else None


def canonical(name):
    key = re.sub(r"\b(ltd|limited|inc|corp|corporation|plc|co|llc)\b\.?", "", name.lower())
    return re.sub(r"[^a-z0-9 ]", "", key).strip()


def sentences(text):
    return [s.strip() for s in SENT_SPLIT.split(text.replace("\n", " ")) if s.strip()]


def extract_deal_structure(text, etype):
    t = text.lower()
    if "all-stock" in t or "stock swap" in t:
        return "All-Stock Transaction"
    elif "all-cash" in t or "cash deal" in t or "cash buyout" in t:
        return "All-Cash Consideration"
    elif "controlling stake" in t or "majority stake" in t:
        return "Controlling Majority Stake"
    elif "unsolicited" in t or "hostile" in t:
        return "Contested Tender Offer"
    elif etype == "IPO":
        return "Primary Public Offering"
    elif etype == "DIVESTITURE":
        return "Asset Carve-out / Divestiture"
    return "Equity Purchase Agreement"


def extract_timeline(text, article):
    d_match = DATE_RE.search(text)
    ann_date = d_match.group(0) if d_match else article.get("published") or "Recent Announcement"
    
    t_match = TIMELINE_RE.search(text)
    effective_timeline = t_match.group(0) if t_match else "Pending Closing Conditions"
    
    status = "Announced"
    t_low = text.lower()
    if "completes" in t_low or "completed" in t_low:
        status = "Completed"
    elif "rejects" in t_low or "fend off" in t_low or "poison pill" in t_low:
        status = "Contested / Hostile"
    elif "close in" in t_low or "later this year" in t_low:
        status = "Pending Closing"
    elif "files" in t_low or "plans" in t_low:
        status = "Regulatory Filing / Pipeline"

    return ann_date, effective_timeline, status


def extract_rationale(text):
    """Extracts strategic reasoning or business rationale from sentences."""
    sents = sentences(text)
    for s in sents:
        if re.search(r"\b(to secure|to expand|to raise|exits non-core|fend off|to bolster|to focus on|synergies|combined entity)\b", s, re.I):
            return s.strip()
    return None


def generate_executive_brief(info, article):
    """
    Synthesizes a high-level, human-readable executive narrative explaining
    the corporate transaction, its commercial scope, timing, and strategic logic.
    """
    etype = info["event_type"]
    val = f" valued at {info['deal_value']}" if info["deal_value"] else ""
    date_str = f"on {info['event_date']}" if info["event_date"] and info["event_date"] != "Recent Announcement" else "recently"
    rationale = info.get("strategic_rationale")

    if etype == "ACQUISITION":
        acq = info["acquirer"] or "The acquiring company"
        tgt = info["target"] or "the target firm"
        brief = f"{acq} agreed to acquire {tgt}{val} {date_str}. "
        if rationale:
            brief += f"{rationale} "
        if info.get("effective_timeline") and info["effective_timeline"] != "Pending Closing Conditions":
            brief += f"Expected timeline: {info['effective_timeline']}."
        return brief.strip()

    elif etype == "MERGER":
        comps = " and ".join(info["companies"]) if info["companies"] else "Both companies"
        brief = f"{comps} have entered into a definitive merger agreement{val} to combine operations. "
        if rationale:
            brief += f"{rationale} "
        brief += f"The transaction was approved by leadership {date_str}."
        return brief.strip()

    elif etype == "DIVESTITURE":
        seller = info["seller"] or "The company"
        asset = info["target"] or "its subsidiary division"
        buyer = f" to {info['buyer']}" if info.get("buyer") else ""
        brief = f"{seller} agreed to sell its {asset} unit{buyer}{val} {date_str}. "
        if rationale:
            brief += f"{rationale} "
        if info.get("effective_timeline"):
            brief += f"Transaction expected to {info['effective_timeline']}."
        return brief.strip()

    elif etype == "HOSTILE_TAKEOVER":
        acq = info["acquirer"] or "The hostile bidder"
        tgt = info["target"] or "the target company"
        brief = f"{acq} launched an unsolicited hostile takeover bid for {tgt}{val}. "
        brief += f"The board of {tgt} has mounted defensive measures (including a poison pill) to fend off the takeover approach."
        return brief.strip()

    elif etype == "EXECUTIVE_CHANGE":
        ppl = info["people"]
        if ppl:
            p_desc = []
            for p in ppl:
                action = "has been appointed as" if p["change"] == "appointed" else "stepped down from the role of"
                p_desc.append(f"{p['name']} {action} {p['role'] or 'executive'}")
            brief = f"{info['companies'][0] if info['companies'] else 'The company'} announced executive leadership transitions: {'; '.join(p_desc)} ({date_str})."
        else:
            brief = f"Leadership transition announced at {info['companies'][0] if info['companies'] else 'the organization'}."
        return brief.strip()

    elif etype == "IPO":
        comp = info["companies"][0] if info["companies"] else "The company"
        brief = f"{comp} filed regulatory draft papers for an Initial Public Offering (IPO) to raise {info['deal_value'] or 'growth capital'}. "
        brief += "The public listing will allow public market investors to participate in the company's equity."
        return brief.strip()

    return article["title"]


def generate_key_highlights(info):
    """Generates structured bullet points tailored for presentation UI cards."""
    highlights = []
    
    # Highlight 1: Deal Scope
    if info["event_type"] == "ACQUISITION":
        highlights.append(f"Transaction Scope: {info['acquirer'] or 'Acquirer'} acquiring {info['target'] or 'Target'}")
    elif info["event_type"] == "MERGER":
        highlights.append(f"Merger Partners: {' & '.join(info['companies'])}")
    elif info["event_type"] == "DIVESTITURE":
        buyer_str = f" ➔ Buyer: {info['buyer']}" if info.get("buyer") else ""
        highlights.append(f"Divestment: {info['seller']} selling {info['target']}{buyer_str}")
    elif info["event_type"] == "HOSTILE_TAKEOVER":
        highlights.append(f"Hostile Bid: {info['acquirer']} targeting {info['target']} (Defenses Deployed)")
    elif info["event_type"] == "EXECUTIVE_CHANGE":
        names = [f"{p['name']} ({p['change']} {p['role'] or ''})".strip() for p in info["people"]]
        highlights.append(f"Leadership Movement: {', '.join(names) if names else 'Executive reshuffle'}")
    elif info["event_type"] == "IPO":
        highlights.append(f"Public Issue: {info['companies'][0] if info['companies'] else 'Issuer'} Draft Filing")

    # Highlight 2: Valuation & Terms
    if info["deal_value"]:
        highlights.append(f"Financial Consideration: {info['deal_value']} ({info['deal_structure']})")
    else:
        highlights.append(f"Deal Structure: {info['deal_structure']}")

    # Highlight 3: Timeline & Governance
    highlights.append(f"Timeline Status: {info['status']} | Date: {info['event_date']}")

    # Highlight 4: Strategic Rationale
    if info.get("strategic_rationale"):
        highlights.append(f"Strategic Rationale: {info['strategic_rationale']}")

    return highlights


def extract_event(article):
    """Returns a rich, fully populated dictionary for one classified article."""
    etype = article.get("event_type", "NO_EVENT")
    text = (article["title"] + ". " + article["text"]).strip()
    sents = sentences(text)

    info = {
        "event_type": etype,
        "event_subtype": article.get("event_subtype", etype),
        "acquirer": None,
        "target": None,
        "seller": None,
        "buyer": None,
        "companies": [],
        "people": [],
        "deal_value": None,
        "deal_structure": extract_deal_structure(text, etype),
        "event_date": None,
        "effective_timeline": None,
        "status": "Announced",
        "strategic_rationale": extract_rationale(text),
        "event_brief": "",
        "key_highlights": [],
        "significance": "HIGH" if etype in ("ACQUISITION", "MERGER", "HOSTILE_TAKEOVER") else "MEDIUM",
    }

    def first(pattern_list):
        pats = pattern_list if isinstance(pattern_list, list) else [pattern_list]
        for s in sents:
            for p in pats:
                m = p.search(s)
                if m:
                    return m, s
        return None, None

    if etype in ("ACQUISITION", "HOSTILE_TAKEOVER"):
        m, s = first([HOSTILE_REJECT, ACQ_ACTIVE, ACQ_PASSIVE])
        if m:
            info["acquirer"], info["target"] = clean_company(m["acq"]), clean_company(m["tgt"])
            info["companies"] = [c for c in (info["acquirer"], info["target"]) if c]
    elif etype == "MERGER":
        m, s = first(MERGE)
        if m:
            info["companies"] = [c for c in (clean_company(m["a"]), clean_company(m["b"])) if c]
            if len(info["companies"]) >= 2:
                info["acquirer"], info["target"] = info["companies"][0], info["companies"][1]
    elif etype == "DIVESTITURE":
        m, s = first(SELL)
        if m:
            info["seller"], info["target"] = clean_company(m["seller"]), clean_company(m["asset"])
            for s2 in sents:
                b = BUYER.search(s2)
                if b and (info["target"] or "") in s2:
                    info["buyer"] = clean_company(b["buyer"])
                    break
            info["companies"] = [c for c in (info["seller"], info["target"], info["buyer"]) if c]
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
                    c_clean = clean_company(d.get("company"))
                    info["people"].append({
                        "name": d["person"],
                        "role": (d.get("role") or "").strip() or None,
                        "company": c_clean,
                        "change": kind
                    })
        if info["people"]:
            c_name = info["people"][0]["company"]
            info["companies"] = [c_name] if c_name else []
    elif etype == "IPO":
        m, _ = first(IPO_RE)
        if m:
            info["companies"] = [clean_company(m["company"])]
            info["target"] = info["companies"][0]

    # Deal value & Timeline
    v = VALUE_RE.search(text)
    info["deal_value"] = v.group(0).strip() if v else None
    
    ann_date, eff_timeline, status = extract_timeline(text, article)
    info["event_date"] = ann_date
    info["effective_timeline"] = eff_timeline
    info["status"] = status

    # Synthesized Brief & Highlights
    info["event_brief"] = generate_executive_brief(info, article)
    info["key_highlights"] = generate_key_highlights(info)
    info["summary"] = info["event_brief"]  # backwards compatibility

    return info


def extract_all(articles):
    events = []
    for a in articles:
        if not a.get("is_corporate_event"):
            continue
        info = extract_event(a)
        info.update({
            "title": a["title"],
            "source": a["source"],
            "url": a["url"],
            "confidence": a["confidence"],
            "raw_text_snippet": a["text"][:400] + ("..." if len(a["text"]) > 400 else "")
        })
        events.append(info)
    return events
