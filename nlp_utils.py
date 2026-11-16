"""Small helpers shared by the notebooks of the project."""

import csv
from pathlib import Path

from spacy.lang.fr.stop_words import STOP_WORDS as FR_STOP_WORDS

ROOT = Path(__file__).resolve().parent
CORPUS = ROOT / "corpus"
CATEGORIES = ["emissions", "energies_renouvelables", "pollution", "politique_climatique"]
KINDS = ["encyclopedia", "news", "discussion", "legal"]


def load_corpus(kinds=None, added=None):
    """Return the corpus as a list of dicts: the metadata columns plus 'text'.

    kinds: e.g. ["encyclopedia", "news"]   (None = all kinds)
    added: e.g. "week1"                    (None = all weeks)
    """
    with open(CORPUS / "metadata.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    docs = []
    for row in rows:
        if kinds and row["kind"] not in kinds:
            continue
        if added and row["added"] != added:
            continue
        row["text"] = (CORPUS / row["file"]).read_text(encoding="utf-8")
        docs.append(row)
    return docs


def preprocess(doc, keep_stopwords=False):
    """Week 6 preprocessing of a spaCy Doc: lemmatize, lowercase, drop punctuation and stop words.

    The lemma is taken from spaCy (which needs the original casing to tag well),
    then lowercased. Numbers and symbols are dropped, words with letters are kept.
    """
    out = []
    for t in doc:
        if t.is_punct or t.is_space or not any(c.isalpha() for c in t.text):
            continue
        # a stop word if its form OR its lemma is in the list ('été' is not, its lemma 'être' is)
        if (t.is_stop or t.lemma_.lower() in FR_STOP_WORDS) and not keep_stopwords:
            continue
        out.append(t.lemma_.lower())
    return out
