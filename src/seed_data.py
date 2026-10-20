"""
Builds a comprehensive, high-quality labelled training dataset for corporate event classification.
Covers 7 distinct event classes with realistic financial terminology, corporate headlines,
executive appointments, regulatory filings, and negative non-event market news.
"""
import csv
import random

COMPANIES = [
    "Zenith Motors Ltd", "Apex Pharma Inc", "Orion Steel Corp", "Nimbus Cloud Inc",
    "Vertex Bank", "Lotus Foods Ltd", "Helios Energy PLC", "Quantum Retail Group",
    "Bluewave Telecom Ltd", "Crescent Textiles Ltd", "Falcon Airlines", "Meridian Insurance Co",
    "Atlas Logistics Ltd", "Pioneer Software Inc", "Sunrise Hospitals Ltd", "Titan Chemicals Corp",
    "Redwood Media Group", "Summit Cement Ltd", "Harbor Shipping Co", "Evergreen Agro Ltd",
    "Reliance Industries", "Tata Consultancy Services", "Infosys Technologies", "HDFC Bank Ltd",
    "Bharti Airtel", "Adani Enterprises", "Wipro Limited", "Mahindra & Mahindra",
    "Novartis AG", "NextGen Robotics Inc", "Global Mining Corp", "Sterling Financial Group"
]

VALUES = [
    "$1.2 billion", "$450 million", "Rs 3,500 crore", "₹820 crore", "$7.8 billion",
    "EUR 600 million", "$95 million", "Rs 12,000 crore", "$3.4 billion", "₹1,500 crore",
    "$500 million", "$2.1 billion", "Rs 4,200 crore", "£350 million"
]

PEOPLE = [
    "Rahul Mehta", "Anita Desai", "John Carter", "Sarah Lopez", "Vikram Rao",
    "Priya Nair", "David Chen", "Meera Iyer", "Arjun Kapoor", "Emily Clark",
    "Rajesh Gopinathan", "Kavita Sharma", "Michael Chang", "Sanjay Singhania", "Sunita Reddy"
]

ROLES = [
    "CEO", "Chief Executive Officer", "CFO", "Chief Financial Officer",
    "Chairman", "Chairperson", "Managing Director", "Chief Technology Officer",
    "Chief Operating Officer", "Executive Director", "President"
]

TEMPLATES = {
    "ACQUISITION": [
        "{A} to acquire {B} for {V}",
        "{A} has agreed to buy {B} in a deal valued at {V}",
        "{A} completes acquisition of {B}",
        "{B} was acquired by {A} for {V}",
        "{A} announces the acquisition of a controlling stake in {B}",
        "{A} acquires {B} to expand its business, deal worth {V}",
        "{A} snaps up rival {B} in {V} deal",
        "{A} signs definitive agreement to acquire {B} for {V}",
        "{A} buys remaining 49% stake in {B} for {V}",
        "{A} to take over operations of {B} in an all-cash buyout worth {V}",
        "{A} completes buyout of {B} after securing antitrust clearance",
        "{A} set to acquire {B} to bolster market leadership, valuing firm at {V}",
        "{A} reaches pact to acquire {B} in {V} transaction",
        "{A} to purchase specialty division of {B} for {V} in cash",
    ],
    "MERGER": [
        "{A} and {B} to merge in a {V} all-stock deal",
        "{A} announces merger with {B}",
        "Board of {A} approves merger with {B} to create an industry giant",
        "{A} and {B} agree to combine operations after merger talks",
        "Shareholders vote on proposed merger of {A} and {B}",
        "{A} to merge with {B}, creating a combined entity worth {V}",
        "{A} and {B} enter into definitive merger agreement",
        "{A} and {B} announce merger of equals valued at {V}",
        "Antitrust regulator approves mega-merger between {A} and {B}",
        "{A} completes statutory merger with {B} following shareholder consent",
        "{A} and {B} join forces in strategic merger to dominate sector",
    ],
    "DIVESTITURE": [
        "{A} to sell its {B} unit for {V}",
        "{A} agrees to divest its stake in {B}",
        "{A} sells its subsidiary {B} to raise funds, deal worth {V}",
        "{A} offloads non-core business {B} for {V}",
        "{A} completes sale of {B} to a private equity firm",
        "{A} to exit {B} by selling its entire holding",
        "{A} in advanced talks to divest its retail division {B}",
        "{A} completes sale of {B} to strategic buyer for {V}",
        "{A} carves out and sells {B} arm to focus on core operations",
        "{A} offloads 30 percent holding in {B} for {V}",
        "{A} to sell its manufacturing facility {B} to reduce balance sheet debt",
    ],
    "HOSTILE_TAKEOVER": [
        "{A} launches hostile takeover bid for {B}",
        "{B} board rejects unsolicited {V} offer from {A}",
        "{A} goes directly to {B} shareholders with a hostile tender offer",
        "{B} adopts poison pill to fend off hostile bid by {A}",
        "{A} makes unsolicited takeover approach for {B}, which resists the bid",
        "Hostile takeover battle escalates as {A} raises offer for {B}",
        "{B} urges shareholders to reject hostile cash offer from {A}",
        "{A} initiates proxy fight in hostile attempt to seize control of {B}",
        "{B} mounts legal defense against unsolicited takeover bid from {A}",
        "{A} launches hostile offer of {V} for {B} without board consent",
    ],
    "EXECUTIVE_CHANGE": [
        "{A} appoints {P} as new {R}",
        "{P} resigns as {R} of {A}",
        "{A} names {P} {R} with immediate effect",
        "{P} steps down as {R} at {A}",
        "{A} announces leadership change as {R} {P} retires",
        "{A} board elevates {P} to {R} after the sudden exit of previous chief",
        "{P} to take over as incoming {R} at {A} next month",
        "{A} confirms departure of long-serving {R} {P}",
        "{P} quits {A} after five years as {R}",
        "{A} designates {P} as executive {R} following board reshuffle",
        "{P} appointed managing director and {R} at {A}",
    ],
    "IPO": [
        "{A} files draft papers for IPO to raise {V}",
        "{A} launches initial public offering, aims to raise {V}",
        "{A} IPO subscribed 20 times on final day",
        "{A} sets price band for its public issue",
        "{A} gets regulator nod for stock market listing and IPO",
        "{A} files Draft Red Herring Prospectus (DRHP) for {V} IPO",
        "{A} debuts on stock exchange with 35% listing gains after blockbuster IPO",
        "{A} to open initial public offering for retail bidding next week",
        "{A} looks to raise {V} in anchor round ahead of landmark IPO",
        "{A} receives SEBI clearance for public listing and share sale",
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
        "{A} posts record volumes and revenue growth this quarter",
        "{A} quarterly net profit falls 8% on higher input costs",
        "Global stock markets trade mixed ahead of US inflation report",
        "{A} signs non-binding memorandum of understanding for cloud services",
        "{A} management discusses long-term sustainability goals at annual meet",
        "{A} unit posted strong operational performance; historical acquisition in 2024",
        "Tech stocks drag Nasdaq lower as bond yields climb",
        "{A} expands retail network with 50 new experience centers",
    ],
}


def build(path="data/training_data.csv", per_class=50, seed=42):
    rnd = random.Random(seed)
    rows = []
    for label, templates in TEMPLATES.items():
        for _ in range(per_class):
            a, b = rnd.sample(COMPANIES, 2)
            v = rnd.choice(VALUES)
            p = rnd.choice(PEOPLE)
            r = rnd.choice(ROLES)
            text = rnd.choice(templates).format(A=a, B=b, V=v, P=p, R=r)
            rows.append((text, label))
    rnd.shuffle(rows)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["text", "label"])
        w.writerows(rows)
    return path


if __name__ == "__main__":
    print("Training dataset built:", build())
