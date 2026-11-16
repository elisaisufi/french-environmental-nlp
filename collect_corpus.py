"""Collect the French environmental corpus.

The corpus grows week by week. Existing files are never renumbered: new texts
are appended (text33.txt, text34.txt, ...) and documented in corpus/metadata.csv.

Kinds of text (Tutorial 2 asks for at least three):
  encyclopedia  introductions of French Wikipedia articles (100-300 words, Week 1 rules)
  news          French Wikinews articles (full article body, not cleaned)
  discussion    Wikipedia talk pages, forum-like (excerpt of ~450 words, not cleaned)
  legal         official texts from French Wikisource (excerpt of ~450 words)

Every text also has a topic category (the label for classification later):
  emissions · energies_renouvelables · pollution · politique_climatique

Usage:
    python collect_corpus.py --week1          # rebuild the Week 1 corpus (8 per category)
    python collect_corpus.py                  # grow: 20 encyclopedia texts per category + other kinds

Only the Python standard library is needed. An internet connection is required.
"""

import argparse
import csv
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

USER_AGENT = "FrenchEnvironmentalNLP/1.0 (university NLP course project; educational use)"
MIN_WORDS, MAX_WORDS = 100, 300      # encyclopedia texts (Tutorial 1)
EXCERPT_WORDS = 450                  # discussion and legal excerpts (Tutorial 2: ~200 words or more)
FIELDS = ["file", "title", "url", "category", "kind", "words", "added",
          "revision_date", "retrieved", "licence", "source"]

# ---------------------------------------------------------------- encyclopedia
# The first titles of each list are the Week 1 texts; later titles grow the corpus.
TOPICS = {
    "emissions": [
        "Gaz à effet de serre", "Dioxyde de carbone", "Méthane", "Empreinte carbone",
        "Bilan carbone", "Effet de serre", "Neutralité carbone",
        "Captage et stockage du carbone", "Protoxyde d'azote", "Déforestation",
        "Puits de carbone", "Hydrofluorocarbure", "Émissions de gaz à effet de serre en France",
        "Combustible fossile", "Réchauffement climatique",
        "Potentiel de réchauffement global", "Compensation carbone", "Marché du carbone",
        "Cycle du carbone", "Acidification des océans", "Pergélisol", "Sobriété énergétique",
        "Empreinte écologique", "Charbon", "Gaz de schiste",
    ],
    "energies_renouvelables": [
        "Énergie renouvelable", "Énergie solaire photovoltaïque", "Énergie éolienne",
        "Hydroélectricité", "Géothermie", "Biomasse (énergie)", "Énergie marémotrice",
        "Transition énergétique", "Éolienne en mer", "Énergie solaire thermique",
        "Biogaz", "Hydrogène vert", "Panneau solaire", "Biocarburant", "Pompe à chaleur",
        "Énergie solaire", "Centrale solaire thermodynamique", "Énergie hydrolienne",
        "Bois énergie", "Méthanisation", "Cellule photovoltaïque", "Stockage de l'énergie",
        "Réseau électrique intelligent", "Agrivoltaïsme",
    ],
    "pollution": [
        "Pollution de l'air", "Pollution de l'eau", "Pollution des sols",
        "Pollution plastique", "Particules en suspension", "Pluie acide", "Smog",
        "Marée noire", "Pollution lumineuse", "Pollution sonore", "Eutrophisation",
        "Microplastique", "Pesticide", "Métal lourd", "Ozone troposphérique",
        "Pollution", "Dioxyde d'azote", "Dioxyde de soufre", "Monoxyde de carbone",
        "Nitrate", "Saturnisme", "Déchet", "Pollution marine",
    ],
    "politique_climatique": [
        "Accord de Paris sur le climat", "Protocole de Kyoto",
        "Conférence des Nations unies sur les changements climatiques",
        "Groupe d'experts intergouvernemental sur l'évolution du climat",
        "Pacte vert pour l'Europe", "Taxe carbone",
        "Système communautaire d'échange de quotas d'émission",
        "Loi climat et résilience", "Convention-cadre des Nations unies sur les changements climatiques",
        "Agence de l'environnement et de la maîtrise de l'énergie",
        "Stratégie nationale bas-carbone", "Convention citoyenne pour le climat",
        "Haut Conseil pour le climat", "Grenelle de l'environnement", "Justice climatique",
        "Conférence de Paris de 2015 sur les changements climatiques", "Protocole de Montréal",
        "Grève scolaire pour le climat", "Principe pollueur-payeur",
        "Programme des Nations unies pour l'environnement",
        "Agence européenne pour l'environnement",
        "Loi relative à la transition énergétique pour la croissance verte",
        "Accord de Kigali", "Plan climat-air-énergie territorial",
    ],
}

# ---------------------------------------------------------------- other kinds
# (kind, site, page title, category, licence)
OTHER = [
    # news: French Wikinews
    ("news", "fr.wikinews.org", "Canada : le gouvernement canadien présente son plan de réduction des émissions de GES d'ici 2030", "emissions", "CC BY 2.5 / CC BY-SA 4.0"),
    ("news", "fr.wikinews.org", "Obama annonce de nouvelles normes pour les véhicules", "emissions", "CC BY 2.5 / CC BY-SA 4.0"),
    ("news", "fr.wikinews.org", "Nucléaire : 69 % des Français pensent à tort que le nucléaire contribue au réchauffement climatique", "emissions", "CC BY 2.5 / CC BY-SA 4.0"),
    ("news", "fr.wikinews.org", "Climat : l'Inde annonce qu'elle vise la neutralité carbone pour 2070", "emissions", "CC BY 2.5 / CC BY-SA 4.0"),
    ("news", "fr.wikinews.org", "France : 100 % d’énergie renouvelable en 2050 ?", "energies_renouvelables", "CC BY 2.5 / CC BY-SA 4.0"),
    ("news", "fr.wikinews.org", "Électricité : la consommation est destiné à augmenter dans le cadre de la transition énergétique", "energies_renouvelables", "CC BY 2.5 / CC BY-SA 4.0"),
    ("news", "fr.wikinews.org", "Énergies renouvelables : les Bretons très favorables aux nouvelles énergies", "energies_renouvelables", "CC BY 2.5 / CC BY-SA 4.0"),
    ("news", "fr.wikinews.org", "Nouveau parc éolien au Québec", "energies_renouvelables", "CC BY 2.5 / CC BY-SA 4.0"),
    ("news", "fr.wikinews.org", "Chine : Pékin en alerte rouge pollution", "pollution", "CC BY 2.5 / CC BY-SA 4.0"),
    ("news", "fr.wikinews.org", "Affaire Erika: la Cour de cassation confirme les condamnations prononcées", "pollution", "CC BY 2.5 / CC BY-SA 4.0"),
    ("news", "fr.wikinews.org", "Zambie : une marée noire dans la rivière Kafue menace des millions de personnes", "pollution", "CC BY 2.5 / CC BY-SA 4.0"),
    ("news", "fr.wikinews.org", "Nouvelle-Zélande : une marée noire menace la faune de la baie de Plenty", "pollution", "CC BY 2.5 / CC BY-SA 4.0"),
    ("news", "fr.wikinews.org", "Union européenne : pas de taxe carbone en juin 2010", "politique_climatique", "CC BY 2.5 / CC BY-SA 4.0"),
    ("news", "fr.wikinews.org", "Suisse : le Parlement s'accorde sur une révision de la loi sur le CO2", "politique_climatique", "CC BY 2.5 / CC BY-SA 4.0"),
    ("news", "fr.wikinews.org", "Un nouveau cycle de négociations sur le climat s'est ouvert à Bangkok", "politique_climatique", "CC BY 2.5 / CC BY-SA 4.0"),
    ("news", "fr.wikinews.org", "Conférence de Copenhague : fin des négociations", "politique_climatique", "CC BY 2.5 / CC BY-SA 4.0"),
    # discussion: Wikipedia talk pages
    ("discussion", "fr.wikipedia.org", "Discussion:Changement climatique", "emissions", "CC BY-SA 4.0"),
    ("discussion", "fr.wikipedia.org", "Discussion:Méthane", "emissions", "CC BY-SA 4.0"),
    ("discussion", "fr.wikipedia.org", "Discussion:Énergie éolienne", "energies_renouvelables", "CC BY-SA 4.0"),
    ("discussion", "fr.wikipedia.org", "Discussion:Énergie solaire photovoltaïque", "energies_renouvelables", "CC BY-SA 4.0"),
    ("discussion", "fr.wikipedia.org", "Discussion:Pollution de l'air", "pollution", "CC BY-SA 4.0"),
    ("discussion", "fr.wikipedia.org", "Discussion:Marée noire", "pollution", "CC BY-SA 4.0"),
    ("discussion", "fr.wikipedia.org", "Discussion:Taxe carbone", "politique_climatique", "CC BY-SA 4.0"),
    ("discussion", "fr.wikipedia.org", "Discussion:Accord de Paris sur le climat", "politique_climatique", "CC BY-SA 4.0"),
    # legal: official texts on Wikisource
    ("legal", "fr.wikisource.org", "Charte de l’environnement", "politique_climatique", "Domaine public (texte officiel)"),
    ("legal", "fr.wikisource.org", "Charte mondiale de la nature", "politique_climatique", "Domaine public (texte officiel)"),
]


# ---------------------------------------------------------------- download
def api(site, params):
    params = {"format": "json", "formatversion": "2", **params}
    req = urllib.request.Request(f"https://{site}/w/api.php?" + urllib.parse.urlencode(params),
                                 headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def fetch_intro(title):
    """Wikipedia lead section as plain text: dict(title, url, rev, extract) or None."""
    page = api("fr.wikipedia.org", {
        "action": "query", "prop": "extracts|info|revisions", "exintro": "1", "explaintext": "1",
        "inprop": "url", "rvprop": "timestamp", "redirects": "1", "titles": title,
    })["query"]["pages"][0]
    if page.get("missing") or not page.get("extract"):
        return None
    return {"title": page["title"], "url": page["fullurl"],
            "rev": page["revisions"][0]["timestamp"], "extract": page["extract"]}


def fetch_html(site, title):
    """Rendered HTML of a page: dict(title, url, rev, html) or None."""
    data = api(site, {"action": "parse", "page": title, "prop": "text|revid", "redirects": "1"})
    if "error" in data:
        return None
    parsed = data["parse"]
    info = api(site, {"action": "query", "prop": "info|revisions", "inprop": "url",
                      "rvprop": "timestamp", "pageids": parsed["pageid"]})["query"]["pages"][0]
    return {"title": parsed["title"], "url": info["fullurl"],
            "rev": info["revisions"][0]["timestamp"], "html": parsed["text"]}


# ---------------------------------------------------------------- text processing
def clean(text):
    """Week 1 cleaning for encyclopedia intros: drop empty lines, collapse spaces, remove '( )'."""
    text = re.sub(r"\(\s*[;,]?\s*\)", "", text)
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def fit_length(text):
    """Keep whole sentences up to MAX_WORDS. Return None if shorter than MIN_WORDS."""
    if len(text.split()) <= MAX_WORDS:
        return text if len(text.split()) >= MIN_WORDS else None
    sentences = re.split(r"(?<=[.!?])\s+", text)
    kept, count = [], 0
    for s in sentences:
        n = len(s.split())
        if count + n > MAX_WORDS:
            break
        kept.append(s)
        count += n
    return " ".join(kept) if count >= MIN_WORDS else None


class _TextExtractor(HTMLParser):
    """Collect the visible text of block elements (p, li, dd, headings) in order.

    No cleaning is done (Tutorial 2): numbers, signatures, dates, URLs and odd
    punctuation stay as they are. Only page furniture is skipped: tables
    (banners), style/script and the '[modifier le code]' edit links.
    """
    BLOCKS = {"p", "li", "dd", "dt", "h2", "h3", "h4", "blockquote", "pre"}
    SKIP = {"table", "style", "script"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lines, self.buf = [], []
        self.depth_block = 0
        self.skip_stack = []          # tags we are skipping (by name)
        self.seen_h2 = False

    def handle_starttag(self, tag, attrs):
        cls = dict(attrs).get("class") or ""
        if self.skip_stack:
            if tag == self.skip_stack[-1][0]:
                self.skip_stack.append((tag, None))
            return
        if tag in self.SKIP or "mw-editsection" in cls:
            self.skip_stack.append((tag, None))
            return
        if tag == "h2":
            self.seen_h2 = True
        if tag in self.BLOCKS:
            self.depth_block += 1
        if tag == "br":
            self.buf.append("\n")

    def handle_endtag(self, tag):
        if self.skip_stack:
            if tag == self.skip_stack[-1][0]:
                self.skip_stack.pop()
            return
        if tag in self.BLOCKS and self.depth_block:
            self.depth_block -= 1
            self._flush(tag)

    def handle_data(self, data):
        if not self.skip_stack and self.depth_block:
            self.buf.append(data)

    def _flush(self, tag):
        text = "".join(self.buf).strip()
        self.buf = []
        if text:
            self.lines.append((tag, self.seen_h2, text))


def html_to_lines(html):
    parser = _TextExtractor()
    parser.feed(html)
    return parser.lines


def excerpt(lines, max_words=EXCERPT_WORDS, min_words=200):
    """Whole lines until about max_words words (but at least min_words when the page has them)."""
    out, n = [], 0
    for text in lines:
        w = len(text.split())
        if n >= min_words and n + w > max_words:
            break
        out.append(text)
        n += w
    return "\n".join(out)


def html_text(kind, html):
    lines = html_to_lines(html)
    if kind == "news":            # the article body: the paragraphs before the first section (Sources, ...);
        # lists before it are the page's sidebar of other headlines, not the article
        return "\n".join(t for tag, after_h2, t in lines if not after_h2 and tag == "p")
    if kind == "discussion":      # the discussions start at the first section heading
        return excerpt([t for tag, after_h2, t in lines if after_h2])
    return excerpt([t for tag, after_h2, t in lines])     # legal


# ---------------------------------------------------------------- corpus files
def load_metadata(out):
    path = out / "metadata.csv"
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:                      # Week 1 metadata had no kind / added columns
        r.setdefault("kind", "encyclopedia")
        r.setdefault("added", "week1")
        r["kind"] = r["kind"] or "encyclopedia"
        r["added"] = r["added"] or "week1"
    return rows


def save_metadata(out, rows):
    with open(out / "metadata.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def add_text(out, rows, text, info, category, kind, licence, source, added):
    filename = f"text{len(rows) + 1:02d}.txt"
    (out / filename).write_text(text + "\n", encoding="utf-8")
    rows.append({
        "file": filename, "title": info["title"], "url": info["url"], "category": category,
        "kind": kind, "words": len(text.split()), "added": added,
        "revision_date": info["rev"][:10], "retrieved": date.today().isoformat(),
        "licence": licence, "source": source,
    })
    print(f"  + {filename} [{kind}/{category}] {info['title'][:60]} ({len(text.split())} words)")


def grow(out, per_category, added, with_other=True, fetchers=None):
    """Append texts until each category has `per_category` encyclopedia texts, then the other kinds.

    `fetchers` lets the caller supply already-downloaded data (same format as fetch_intro /
    fetch_html); by default the data is downloaded from the API.
    """
    f_intro, f_html = fetchers or (fetch_intro, fetch_html)
    rows = load_metadata(out)
    have_titles = {r["title"] for r in rows}
    for category, titles in TOPICS.items():
        count = sum(r["category"] == category and r["kind"] == "encyclopedia" for r in rows)
        for title in titles:
            if count >= per_category:
                break
            info = f_intro(title)
            if info is None or info["title"] in have_titles:
                continue
            text = fit_length(clean(info["extract"]))
            if text is None:
                continue
            add_text(out, rows, text, info, category, "encyclopedia", "CC BY-SA 4.0",
                     "Wikipédia (fr)", added)
            have_titles.add(info["title"])
            count += 1
            if fetchers is None:
                time.sleep(0.3)
    if with_other:
        for kind, site, title, category, licence in OTHER:
            info = f_html(site, title)
            if info is None or info["title"] in have_titles:
                continue
            text = html_text(kind, info["html"])
            if len(text.split()) < 100:
                print(f"  - {title}: too short, skipped")
                continue
            source = {"fr.wikinews.org": "Wikinews (fr)", "fr.wikisource.org": "Wikisource (fr)",
                      "fr.wikipedia.org": "Wikipédia (fr), page de discussion"}[site]
            add_text(out, rows, text, info, category, kind, licence, source, added)
            have_titles.add(info["title"])
            if fetchers is None:
                time.sleep(0.3)
    save_metadata(out, rows)
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--week1", action="store_true", help="rebuild the Week 1 corpus from scratch")
    parser.add_argument("--per-category", type=int, default=20)
    parser.add_argument("--added", default="week2", help="label stored in the 'added' column")
    parser.add_argument("--out", default="corpus")
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(exist_ok=True)
    if args.week1:
        for f in out.glob("*"):
            f.unlink()
        rows = grow(out, 8, "week1", with_other=False)
    else:
        rows = grow(out, args.per_category, args.added)
    kinds = {}
    for r in rows:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    print(f"\n{len(rows)} texts in {out}/: {kinds}")


if __name__ == "__main__":
    main()
