"""
Task (d): Create a tree of a Company and its subsidiaries.

Relationships are mined from article text with patterns such as
  "X, a subsidiary of Y"  |  "Y's subsidiary X"  |  "X, owned by Y"
  "Y holds a 60% stake in X"  |  "Y acquired X" (acquirer becomes the parent)
and stored in a directed graph (parent -> child) built with networkx.
"""
import json
import re

import networkx as nx

from .extractor import COMPANY, clean_company, canonical, sentences

OWN = r"(?:wholly[- ]owned\s+|majority[- ]owned\s+|fully[- ]owned\s+)?"
KIND = r"(?:subsidiary|unit|arm|division|affiliate)"

REL_PATTERNS = [
    ("subsidiary",
     re.compile(rf"(?P<child>{COMPANY}),?\s+(?:a|an|the)\s+{OWN}{KIND}\s+of\s+(?P<parent>{COMPANY})")),
    ("subsidiary",
     re.compile(rf"(?P<parent>{COMPANY})(?:'s|’s)\s+{OWN}{KIND}\s*,?\s+(?P<child>{COMPANY})")),
    ("subsidiary",
     re.compile(rf"(?P<child>{COMPANY}),?\s+(?:which\s+is\s+)?{OWN}owned\s+by\s+(?P<parent>{COMPANY})")),
    ("stake",
     re.compile(rf"(?P<parent>{COMPANY})\s+(?:holds|owns)\s+(?:a\s+)?(?P<pct>\d+(?:\.\d+)?)\s?(?:%|per\s?cent)"
                rf"\s+(?:stake\s+)?in\s+(?P<child>{COMPANY})")),
]


class CompanyGraph:
    def __init__(self):
        self.g = nx.DiGraph()
        self.display = {}

    def _node(self, name):
        key = canonical(name)
        self.display.setdefault(key, name)
        self.g.add_node(key)
        return key

    def add(self, parent, child, relation, source, pct=None):
        parent, child = clean_company(parent), clean_company(child)
        if not parent or not child:
            return
        p, c = self._node(parent), self._node(child)
        if p == c or self.g.has_edge(c, p):  # ignore self-loops / contradictions
            return
        if self.g.has_edge(p, c):
            return
        former = None
        if self.g.in_degree(c):
            if relation != "acquisition":      # a company keeps one parent -> stays a tree
                return
            old = list(self.g.predecessors(c))   # acquisition = new owner replaces old parent
            former = self.display[old[0]]
            self.g.remove_edges_from([(o, c) for o in old])
        self.g.add_edge(p, c, relation=relation, source=source, pct=pct, former_parent=former)

    def add_from_articles(self, articles, events):
        for a in articles:
            for s in sentences(a["title"] + ". " + a["text"]):
                for rel, pat in REL_PATTERNS:
                    for m in pat.finditer(s):
                        self.add(m["parent"], m["child"], rel, a["url"],
                                 pct=m.groupdict().get("pct"))
        # completed deals also create parent -> child links
        for e in events:
            if e["event_type"] in ("ACQUISITION", "HOSTILE_TAKEOVER") and e["acquirer"] and e["target"]:
                self.add(e["acquirer"], e["target"], "acquisition", e["url"])

    # ---------- outputs ----------
    def roots(self):
        return sorted((n for n in self.g if self.g.in_degree(n) == 0 and self.g.out_degree(n) > 0),
                      key=lambda n: -len(nx.descendants(self.g, n)))

    def nested(self, node):
        return {"company": self.display[node],
                "subsidiaries": [dict(self.nested(c), relation=self.g[node][c]["relation"])
                                 for c in sorted(self.g.successors(node))]}

    def to_json(self):
        return [self.nested(r) for r in self.roots()]

    def to_text(self, ascii_only=False):
        lines = []

        def walk(n, prefix="", last=True, root=False):
            label = self.display[n]
            if not root:
                e = self.g[self._parent[n]][n]
                extra = f"{e['pct']}% stake" if e.get("pct") else e["relation"]
                if e.get("former_parent"):
                    extra += f"; formerly under {e['former_parent']}"
                label += f"  [{extra}]"
            branch = ("\\-- " if last else "+-- ") if ascii_only else ("└── " if last else "├── ")
            lines.append(label if root else prefix + branch + label)
            kids = sorted(self.g.successors(n))
            vert = ("    " if last else "|   ") if ascii_only else ("    " if last else "│   ")
            for i, c in enumerate(kids):
                walk(c, prefix + ("" if root else vert), i == len(kids) - 1)

        self._parent = {c: p for p, c in self.g.edges}
        for r in self.roots():
            walk(r, root=True)
            lines.append("")
        return "\n".join(lines) if lines else "(no parent/subsidiary relations found)"

    def draw(self, path):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        if not self.g.number_of_edges():
            return
        depth, pos_x = {}, {}
        for r in self.roots():
            depth[r] = 0
            for n, d in nx.single_source_shortest_path_length(self.g, r).items():
                depth[n] = max(depth.get(n, 0), d)
        layers = {}
        for n, d in depth.items():
            layers.setdefault(d, []).append(n)
        pos = {}
        for d, nodes in layers.items():
            for i, n in enumerate(sorted(nodes)):
                pos[n] = ((i + 1) / (len(nodes) + 1) * 10 * max(1, len(layers[0]) / 2), -d)
        fig, ax = plt.subplots(figsize=(max(10, 3 * len(layers[0])), 2.2 * len(layers) + 1))
        self.g.remove_nodes_from(list(nx.isolates(self.g)))
        pos = {n: xy for n, xy in pos.items() if n in self.g}
        nx.draw_networkx_edges(self.g, pos, ax=ax, arrows=True, arrowsize=14, edge_color="#666")
        nx.draw_networkx_nodes(self.g, pos, ax=ax, node_size=300, node_color="#4C78A8")
        nx.draw_networkx_labels(self.g, pos, labels={n: self.display[n] for n in self.g}, ax=ax,
                                font_size=8, verticalalignment="bottom")
        ax.set_title("Company -> Subsidiary tree")
        ax.axis("off")
        fig.tight_layout()
        fig.savefig(path, dpi=140)
        plt.close(fig)

    def save(self, folder="output"):
        self.g.remove_nodes_from(list(nx.isolates(self.g)))
        with open(f"{folder}/company_tree.json", "w", encoding="utf-8") as f:
            json.dump(self.to_json(), f, indent=2, ensure_ascii=False)
        with open(f"{folder}/company_tree.txt", "w", encoding="utf-8") as f:
            f.write(self.to_text())
        self.draw(f"{folder}/company_tree.png")
