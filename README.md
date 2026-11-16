# French Environmental Text Intelligence 🌿

**Automatic classification and information retrieval in French environmental texts**

NLP course project (AI Engineering, Group 3: French). We build a French corpus about the environment and develop it week by week, following the course pipeline: corpus → tokenization & n-grams → TF-IDF → topic classification → search engine.

## Idea

A user types a topic in French (for example *énergie solaire* or *pollution de l'air*), and the system:
1. **classifies** documents into four themes: émissions · énergies renouvelables · pollution · politique climatique
2. **retrieves** the most relevant documents for the query (TF-IDF + cosine similarity)

## Corpus

| | |
|---|---|
| Language | French |
| Text type | Introductions of French Wikipedia articles (100–300 words each) |
| Size | 20+ texts in Week 1 → ~100 texts in Week 3 (about 25 per category) |
| Format | One UTF-8 `.txt` file per text (`corpus/text01.txt`, …) |
| Metadata | `corpus/metadata.csv`: title, URL, category, revision date, retrieval date, licence |
| Licence | Texts: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) (Wikipédia contributors) |

## Project structure

```
collect_corpus.py      # downloads the corpus from the French Wikipedia API
week1_corpus.ipynb     # Tutorial 1: spaCy setup, displaCy, corpus statistics, quality checks
corpus/                # text01.txt … + metadata.csv
images/                # displaCy dependency and entity visualizations
requirements.txt
```

## How to run

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download fr_core_news_md

python collect_corpus.py                    # Week 1: 8 texts per category (32 texts)
python collect_corpus.py --per-category 25  # Week 3: ~100 texts
```

Then open `week1_corpus.ipynb` in VS Code or Jupyter and choose **Restart and Run All**.

## Roadmap

- [x] **Week 1** — Corpus building, spaCy French pipeline, displaCy, quality checks
- [ ] **Week 2** — Tokenization and n-grams (French elision: *l'énergie*, *d'émissions*)
- [ ] **Week 3** — Grow the corpus to ~100 texts, frequency analysis, TF-IDF
- [ ] Topic classification (4 classes) with precision / recall / F1
- [ ] Information retrieval: query → ranked documents, evaluated with Precision@5 on hand-labelled queries
- [ ] Possible extension: official sources (ADEME, vie-publique.fr, EU documents) after checking their licences
