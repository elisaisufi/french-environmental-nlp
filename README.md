# French Environmental Text Intelligence 🌿

**Automatic classification and information retrieval in French environmental texts**

NLP course project (AI Engineering, Group 3: French). We build a French corpus about the environment and develop it week by week with the techniques of the course, up to a **search engine** and a **topic classifier**.

> 👉 New here? Read **[GUIDE.md](GUIDE.md)**: it explains the whole project in plain words.

## Results at a glance

| | Result |
|---|---|
| Corpus | 107 texts, 4 kinds (encyclopedia, news, discussion, legal), 4 topics, ~33,000 tokens |
| Best French tokenizer (hand-made gold standard) | our regex tokenizer F1 1.00 · spaCy 0.99 · NLTK 0.91 · `split()` 0.75 |
| POS tagging on UD French-GSD | spaCy 94.5 % · most-frequent-tag baseline 85.6 % · NLTK (English) 32 % |
| Search engine (14 queries, lemmas + TF-IDF) | Precision@5 0.56 · Recall@10 0.76 · MRR 0.95 |
| Topic classifier (linear SVM, 5-fold CV) | macro F1 0.84 · accuracy 0.85 (baseline F1 0.16) |

## Corpus

| Kind | Source | Texts | Licence |
|---|---|---|---|
| encyclopedia | French Wikipedia (introductions, 100–300 words) | 81 | CC BY-SA 4.0 |
| news | French Wikinews | 16 | CC BY 2.5 / CC BY-SA 4.0 |
| discussion | Wikipedia talk pages (excerpts, not cleaned) | 8 | CC BY-SA 4.0 |
| legal | Wikisource: Charte de l'environnement, Charte mondiale de la nature | 2 | public domain |

Topics: **émissions · énergies renouvelables · pollution · politique climatique**. Every text is a UTF-8 file in `corpus/`; title, URL, topic, kind, date and licence are in `corpus/metadata.csv`. The treebank in `data/` is [UD French-GSD](https://github.com/UniversalDependencies/UD_French-GSD) (CC BY-SA 4.0).

## Project structure

```
collect_corpus.py                         downloads and grows the corpus (Wikipedia, Wikinews, Wikisource APIs)
nlp_utils.py                              load_corpus() and preprocess(), shared by the notebooks
week1_corpus.ipynb                        Tutorial 1: spaCy, displaCy, corpus statistics, quality checks
week2_tokenization.ipynb                  Tutorial 2 (Parts 1-2), own regex tokenizer, n-grams, Zipf's law
week3_lab3_stemming_lemmatization.ipynb   Lab 3: stemming, lemmatization, WordNet + French corpus
week6_pos_stopwords.ipynb                 POS tagging, tagger evaluation, stop words, CoNLL-U
project_search_classification.ipynb       TF-IDF search engine + topic classifier, with evaluation
corpus/  data/  images/                   texts + metadata · treebank + CoNLL-U · figures
GUIDE.md                                  plain-language explanation of everything
```

## How to run

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download fr_core_news_md
python -m spacy download en_core_web_md     # Lab 3 (English exercises)
```

Open a notebook in VS Code or Jupyter, select the `.venv` kernel, then **Restart and Run All**. The notebooks are saved with their outputs, so they can also be read without running them. A few cells need internet (Hugging Face subwords: `pip install transformers sentencepiece`; the Guardian article in Lab 3); they are skipped automatically without a connection.

To grow the corpus: `python collect_corpus.py --per-category 25` (new texts are appended; existing files are never renumbered).

## Roadmap

- [x] **Week 1:** corpus, spaCy French pipeline, displaCy, quality checks
- [x] **Week 2:** tokenizers compared on a gold standard, own regex tokenizer, sentence splitting, n-grams, bigram LM, Zipf
- [x] **Week 3:** stemming vs lemmatization (English + French), WordNet and French WordNet (OMW)
- [x] **Week 6:** POS tagging and evaluation on UD French-GSD, stop words, CoNLL-U
- [x] **Project preview:** TF-IDF search (Precision@5, Recall@10, MRR) and topic classification (cross-validated F1)
- [ ] Named entity recognition (ADEME, GIEC, COP21, places, dates)
- [ ] Query expansion with synonyms / embeddings, BM25
- [ ] More news and discussion texts; official sources (ADEME, vie-publique.fr, EU) after checking licences
- [ ] Multi-label topics and a small web interface
