"""
Task (d): Create a visually stunning tree of a Company and its subsidiaries.

Relationships are mined from article text with patterns such as:
  - "X, a subsidiary of Y"  |  "Y's subsidiary X"  |  "X, owned by Y"
  - "Y holds a 60% stake in X"
  - "Y acquired X" (acquirer becomes the new parent, with provenance tracking)

Renders:
  1. High-Resolution Visual Diagram (output/company_tree.png) with executive dark-slate styling,
     rounded card badges, distinct entity colors, and legible edge annotations.
  2. Hierarchical Text representation (Unicode / ASCII fallback).
  3. Structured nested JSON hierarchy.
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
        if p == c or self.g.has_edge(c, p):  # ignore self-loops / circular cycles
            return
        if self.g.has_edge(p, c):
            return
        former = None
        if self.g.in_degree(c):
            if relation != "acquisition":
                return
            old = list(self.g.predecessors(c))
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
        
        # Completed deals also establish new parent -> subsidiary links
        for e in events:
            if e["event_type"] in ("ACQUISITION", "HOSTILE_TAKEOVER") and e.get("acquirer") and e.get("target"):
                self.add(e["acquirer"], e["target"], "acquisition", e.get("url", ""))

    # ---------- outputs ----------
    def roots(self):
        return sorted((n for n in self.g if self.g.in_degree(n) == 0 and self.g.out_degree(n) > 0),
                      key=lambda n: -len(nx.descendants(self.g, n)))

    def nested(self, node):
        return {
            "company": self.display[node],
            "is_root": self.g.in_degree(node) == 0,
            "subsidiaries": [
                dict(self.nested(c),
                     relation=self.g[node][c]["relation"],
                     pct=self.g[node][c].get("pct"),
                     former_parent=self.g[node][c].get("former_parent"))
                for c in sorted(self.g.successors(node))
            ]
        }

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
        """
        Renders a visually striking, executive dark-themed hierarchy diagram
        with rounded card badges, distinct colors, and legible edge pills.
        """
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches

        if not self.g.number_of_edges():
            return

        self.g.remove_nodes_from(list(nx.isolates(self.g)))
        roots = self.roots()
        if not roots:
            return

        # Calculate hierarchical tree layers
        depth = {}
        for r in roots:
            depth[r] = 0
            for n, d in nx.single_source_shortest_path_length(self.g, r).items():
                depth[n] = max(depth.get(n, 0), d)

        layers = {}
        for n, d in depth.items():
            layers.setdefault(d, []).append(n)

        # Distribute node coordinates cleanly across tiers
        pos = {}
        max_layer_size = max(len(nodes) for nodes in layers.values())
        total_width = max(14, max_layer_size * 3.4)
        
        for d, nodes in layers.items():
            k = len(nodes)
            for i, n in enumerate(sorted(nodes)):
                x = (i + 1) * (total_width / (k + 1))
                y = -d * 2.6
                pos[n] = (x, y)

        fig_height = max(7, len(layers) * 2.8 + 2.5)
        fig, ax = plt.subplots(figsize=(total_width, fig_height), facecolor="#0B132B")
        ax.set_facecolor("#0B132B")

        # Color palette
        COLOR_ROOT = "#4F46E5"        # Indigo
        COLOR_ACQ = "#D97706"         # Amber
        COLOR_SUB = "#0D9488"         # Teal
        EDGE_COLOR = "#64748B"        # Slate grey

        # 1. Draw smooth directed edges with badges
        for u, v, data in self.g.edges(data=True):
            p1 = pos[u]
            p2 = pos[v]
            rel = data.get("relation", "subsidiary")
            pct = data.get("pct")
            former = data.get("former_parent")

            # Determine label text
            if pct:
                edge_text = f"{pct}% Stake"
            elif rel == "acquisition":
                edge_text = "Acquired" + (f" (ex-{former[:10]})" if former else "")
            else:
                edge_text = "Subsidiary"

            # Draw curved arrow
            rad = 0.08 if p1[0] <= p2[0] else -0.08
            ax.annotate(
                "",
                xy=(p2[0], p2[1] + 0.35),
                xytext=(p1[0], p1[1] - 0.35),
                arrowprops=dict(
                    arrowstyle="->,head_width=0.4,head_length=0.6",
                    color=EDGE_COLOR,
                    lw=1.8,
                    connectionstyle=f"arc3,rad={rad}",
                    shrinkA=12,
                    shrinkB=12
                )
            )

            # Draw edge badge pill at midpoint
            mx = (p1[0] + p2[0]) / 2.0
            my = (p1[1] + p2[1]) / 2.0
            ax.text(
                mx, my,
                f" {edge_text} ",
                fontsize=7.5,
                fontweight="medium",
                color="#E2E8F0",
                ha="center",
                va="center",
                bbox=dict(boxstyle="round,pad=0.3", fc="#1E293B", ec="#334155", lw=1.2, alpha=0.92)
            )

        # 2. Draw styled corporate node cards
        for n, (x, y) in pos.items():
            is_root = (self.g.in_degree(n) == 0)
            in_edges = list(self.g.in_edges(n, data=True))
            is_acq = any(e[2].get("relation") == "acquisition" for e in in_edges)

            if is_root:
                bg_color = COLOR_ROOT
                role_tag = "HOLDING / PARENT"
            elif is_acq:
                bg_color = COLOR_ACQ
                role_tag = "ACQUIRED SUBSIDIARY"
            else:
                bg_color = COLOR_SUB
                role_tag = "OPERATING UNIT"

            name = self.display[n]
            node_label = f"{name}\n[{role_tag}]"

            # Draw card box
            ax.text(
                x, y,
                node_label,
                fontsize=9 if is_root else 8.5,
                fontweight="bold" if is_root else "semibold",
                color="#FFFFFF",
                ha="center",
                va="center",
                bbox=dict(
                    boxstyle="round,pad=0.55,rounding_size=0.35",
                    fc=bg_color,
                    ec="#FFFFFF",
                    lw=1.4 if is_root else 1.0,
                    alpha=0.95
                )
            )

        # Title and Header Decoration
        ax.set_title(
            "CORPORATE OWNERSHIP & M&A SUBSIDIARY HIERARCHY",
            fontsize=14,
            fontweight="bold",
            color="#F8FAFC",
            pad=20,
            loc="center"
        )

        # Legend at top right
        legend_patches = [
            patches.Patch(color=COLOR_ROOT, label="Holding / Ultimate Parent"),
            patches.Patch(color=COLOR_SUB, label="Operating Subsidiary"),
            patches.Patch(color=COLOR_ACQ, label="Acquired / M&A Unit"),
        ]
        ax.legend(
            handles=legend_patches,
            loc="upper right",
            facecolor="#1E293B",
            edgecolor="#334155",
            fontsize=8,
            labelcolor="#E2E8F0"
        )

        ax.set_xlim(0, total_width)
        y_vals = [p[1] for p in pos.values()]
        ax.set_ylim(min(y_vals) - 1.2, max(y_vals) + 1.2)
        ax.axis("off")

        fig.tight_layout()
        fig.savefig(path, dpi=180, facecolor=fig.get_facecolor(), edgecolor="none")
        plt.close(fig)

    def save(self, folder="output"):
        self.g.remove_nodes_from(list(nx.isolates(self.g)))
        with open(f"{folder}/company_tree.json", "w", encoding="utf-8") as f:
            json.dump(self.to_json(), f, indent=2, ensure_ascii=False)
        with open(f"{folder}/company_tree.txt", "w", encoding="utf-8") as f:
            f.write(self.to_text())
        self.draw(f"{folder}/company_tree.png")
