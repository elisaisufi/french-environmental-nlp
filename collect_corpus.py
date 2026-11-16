"""Collect a small French environmental corpus from French Wikipedia.

Each text is the introduction (lead section) of one French Wikipedia article.
Texts are saved as UTF-8 .txt files (text01.txt, text02.txt, ...) in corpus/,
and every text is documented in corpus/metadata.csv (title, URL, date, licence,
category) as required by Tutorial 1, section 6.2.

Usage:
    python collect_corpus.py            # default: up to 8 texts per category
    python collect_corpus.py --per-category 25   # grow towards ~100 texts (Week 3)

Only the Python standard library is needed.
"""

import argparse
import csv
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

API = "https://fr.wikipedia.org/w/api.php"
USER_AGENT = "FrenchEnvironmentalNLP/1.0 (university NLP course project; educational use)"
LICENCE = "CC BY-SA 4.0"
MIN_WORDS, MAX_WORDS = 100, 300

# One text type for the whole corpus: introductions of French Wikipedia articles.
# Four categories, used later as labels for topic classification.
TOPICS = {
    "emissions": [
        "Gaz à effet de serre", "Dioxyde de carbone", "Méthane", "Empreinte carbone",
        "Bilan carbone", "Effet de serre", "Neutralité carbone",
        "Captage et stockage du carbone", "Protoxyde d'azote", "Déforestation",
        "Puits de carbone", "Hydrofluorocarbure", "Émissions de gaz à effet de serre en France",
        "Combustible fossile", "Réchauffement climatique",
    ],
    "energies_renouvelables": [
        "Énergie renouvelable", "Énergie solaire photovoltaïque", "Énergie éolienne",
        "Hydroélectricité", "Géothermie", "Énergie de la biomasse", "Énergie marémotrice",
        "Transition énergétique", "Éolienne en mer", "Énergie solaire thermique",
        "Biogaz", "Hydrogène vert", "Panneau solaire", "Biocarburant", "Pompe à chaleur",
    ],
    "pollution": [
        "Pollution de l'air", "Pollution de l'eau", "Pollution des sols",
        "Pollution plastique", "Particules en suspension", "Pluie acide", "Smog",
        "Marée noire", "Pollution lumineuse", "Pollution sonore", "Eutrophisation",
        "Microplastique", "Pesticide", "Métal lourd", "Ozone troposphérique",
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
        "Haut Conseil pour le climat", "Finance climat", "Justice climatique",
    ],
}


def fetch_intro(title):
    """Return (title, url, revision timestamp, plain-text intro) or None."""
    params = {
        "action": "query", "format": "json", "formatversion": "2",
        "prop": "extracts|info|revisions", "exintro": "1", "explaintext": "1",
        "inprop": "url", "rvprop": "timestamp", "redirects": "1", "titles": title,
    }
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(params),
                                 headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    page = data["query"]["pages"][0]
    if page.get("missing") or not page.get("extract"):
        return None
    return page["title"], page["fullurl"], page["revisions"][0]["timestamp"], page["extract"]


def clean(text):
    """Basic cleaning: drop empty lines, collapse spaces, remove empty brackets."""
    text = re.sub(r"\(\s*[;,]?\s*\)", "", text)          # "( )" left by removed pronunciations
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-category", type=int, default=8)
    parser.add_argument("--out", default="corpus")
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(exist_ok=True)
    rows, n = [], 0
    for category, titles in TOPICS.items():
        kept = 0
        for title in titles:
            if kept >= args.per_category:
                break
            try:
                result = fetch_intro(title)
            except Exception as exc:  # network errors etc.
                print(f"  ! {title}: {exc}")
                continue
            if result is None:
                print(f"  - {title}: no page found, skipped")
                continue
            real_title, url, revision, extract = result
            text = fit_length(clean(extract))
            if text is None:
                print(f"  - {real_title}: intro shorter than {MIN_WORDS} words, skipped")
                continue
            n += 1
            kept += 1
            filename = f"text{n:02d}.txt"
            (out / filename).write_text(text + "\n", encoding="utf-8")
            rows.append({
                "file": filename, "title": real_title, "url": url,
                "category": category, "words": len(text.split()),
                "revision_date": revision[:10], "retrieved": date.today().isoformat(),
                "licence": LICENCE, "source": "Wikipédia (fr)",
            })
            print(f"  + {filename}  [{category}]  {real_title} ({len(text.split())} words)")
            time.sleep(0.5)  # be polite to the API
        print(f"{category}: {kept} texts")

    with open(out / "metadata.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nSaved {len(rows)} texts and metadata.csv in {out}/")


if __name__ == "__main__":
    main()
