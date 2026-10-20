"""
Builds a labelled training set for the event classifier.

Real labelled financial-news data is hard to get for free, so we create a seed
dataset from sentence templates (synthetic). You can improve accuracy by adding
real, hand-labelled headlines to data/training_data.csv.
"""
import csv
import random

COMPANIES = [
    "Zenith Motors Ltd", "Apex Pharma Inc", "Orion Steel Corp", "Nimbus Cloud Inc",
    "Vertex Bank", "Lotus Foods Ltd", "Helios Energy PLC", "Quantum Retail Group",
    "Bluewave Telecom Ltd", "Crescent Textiles Ltd", "Falcon Airlines", "Meridian Insurance Co",
    "Atlas Logistics Ltd", "Pioneer Software Inc", "Sunrise Hospitals Ltd", "Titan Chemicals Corp",
    "Redwood Media Group", "Summit Cement Ltd", "Harbor Shipping Co", "Evergreen Agro Ltd",
]
VALUES = ["$1.2 billion", "$450 million", "Rs 3,500 crore", "₹820 crore", "$7.8 billion",
          "EUR 600 million", "$95 million", "Rs 12,000 crore"]
PEOPLE = ["Rahul Mehta", "Anita Desai", "John Carter", "Sarah Lopez", "Vikram Rao",
          "Priya Nair", "David Chen", "Meera Iyer", "Arjun Kapoor", "Emily Clark"]
ROLES = ["CEO", "CFO", "Chairman", "Managing Director", "Chief Technology Officer", "COO"]

TEMPLATES = {
    "ACQUISITION": [
        "{A} to acquire {B} for {V}",
        "{A} has agreed to buy {B} in a deal valued at {V}",
        "{A} completes acquisition of {B}",
        "{B} was acquired by {A} for {V}",
        "{A} announces the acquisition of a controlling stake in {B}",
        "{A} acquires {B} to expand its business, deal worth {V}",
        "{A} snaps up rival {B} in {V} deal",
    ],
    "MERGER": [
        "{A} and {B} to merge in a {V} all-stock deal",
        "{A} announces merger with {B}",
        "Board of {A} approves merger with {B} to create an industry giant",
        "{A} and {B} agree to combine operations after merger talks",
        "Shareholders vote on proposed merger of {A} and {B}",
        "{A} to merge with {B}, creating a combined entity worth {V}",
    ],
    "DIVESTITURE": [
        "{A} to sell its {B} unit for {V}",
        "{A} agrees to divest its stake in {B}",
        "{A} sells its subsidiary {B} to raise funds, deal worth {V}",
        "{A} offloads non-core business {B} for {V}",
        "{A} completes sale of {B} to a private equity firm",
        "{A} to exit {B} by selling its entire holding",
    ],
    "HOSTILE_TAKEOVER": [
        "{A} launches hostile takeover bid for {B}",
        "{B} board rejects unsolicited {V} offer from {A}",
        "{A} goes directly to {B} shareholders with a hostile offer",
        "{B} adopts poison pill to fend off hostile bid by {A}",
        "{A} makes unsolicited takeover approach for {B}, which resists the bid",
        "Hostile takeover battle escalates as {A} raises offer for {B}",
    ],
    "EXECUTIVE_CHANGE": [
        "{A} appoints {P} as new {R}",
        "{P} resigns as {R} of {A}",
        "{A} names {P} {R} with immediate effect",
        "{P} steps down as {R} at {A}",
        "{A} announces leadership change as {R} {P} retires",
        "{A} board elevates {P} to {R} after the sudden exit of the previous chief",
    ],
    "IPO": [
        "{A} files draft papers for IPO to raise {V}",
        "{A} launches initial public offering, aims to raise {V}",
        "{A} IPO subscribed 20 times on final day",
        "{A} sets price band for its public issue",
        "{A} gets regulator nod for stock market listing and IPO",
    ],
    "NO_EVENT": [
        "{A} reports quarterly profit rise of 12 percent",
        "Sensex and Nifty close higher as banking stocks rally",
        "{A} launches new product line for the festive season",
        "Oil prices slip as demand outlook weakens",
        "Central bank keeps interest rates unchanged",
        "{A} shares rise after analysts upgrade the stock",
        "Inflation eases to a three-month low, data shows",
        "{A} opens new factory to boost production capacity",
        "Rupee weakens against the dollar amid foreign outflows",
        "{A} wins a large infrastructure order worth {V}",
        "Gold prices hit record high on safe haven demand",
        "{A} expects strong demand in the coming year, says management",
        "Government announces new tax rules for small businesses",
        "{A} declares an interim dividend for shareholders",
    ],
}


def build(path="data/training_data.csv", per_class=40, seed=42):
    rnd = random.Random(seed)
    rows = []
    for label, templates in TEMPLATES.items():
        for _ in range(per_class):
            a, b = rnd.sample(COMPANIES, 2)
            text = rnd.choice(templates).format(
                A=a, B=b, V=rnd.choice(VALUES), P=rnd.choice(PEOPLE), R=rnd.choice(ROLES))
            rows.append((text, label))
    rnd.shuffle(rows)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["text", "label"])
        w.writerows(rows)
    return path


if __name__ == "__main__":
    print("written", build())
