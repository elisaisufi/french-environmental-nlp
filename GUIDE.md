# Guide: what this project is and what everything does

This guide explains the whole project in plain words: what we built, why, what the results mean, and what to say when someone asks.

---

## 1. The project in four sentences

We collected **107 French texts about the environment** (Wikipedia, news, discussions, official texts) and labelled each one with a topic: *emissions*, *renewable energy*, *pollution* or *climate policy*. Week by week, we apply the course's techniques to them: cutting text into words (tokenization), reducing words to a base form (stemming, lemmatization), grammatical tags (POS) and stop words. At the end, these steps feed two applications: a **search engine** (type *énergie solaire*, get the best documents) and a **classifier** (the computer guesses the topic of a text). Every step is **measured**, not just shown, so we can say which choice works better and why.

---

## 2. The files

| File / folder | What it is |
|---|---|
| `corpus/` | The texts: `text01.txt` … `text107.txt`, one per file, in UTF-8 |
| `corpus/metadata.csv` | One row per text: title, web address, topic, kind of text, number of words, date, licence |
| `collect_corpus.py` | The script that downloads the texts from Wikipedia, Wikinews and Wikisource |
| `nlp_utils.py` | Two small helpers that every notebook uses: `load_corpus()` and `preprocess()` |
| `week1_corpus.ipynb` | Tutorial 1: spaCy setup, first statistics, displaCy pictures |
| `week2_tokenization.ipynb` | Tutorial 2 + Week 2 lecture: tokenizers, sentences, n-grams, Zipf's law |
| `week3_lab3_stemming_lemmatization.ipynb` | Lab 3: stemming, lemmatization, WordNet (+ the same on our French corpus) |
| `week6_pos_stopwords.ipynb` | Week 6 homework: POS tagging, stop words, CoNLL-U |
| `project_search_classification.ipynb` | **The project itself:** search engine and topic classifier, with evaluation |
| `data/` | The French treebank UD French-GSD (gold POS tags, to evaluate taggers) + our corpus in CoNLL-U format |
| `images/` | Charts and pictures saved by the notebooks |
| `corpus_overview.csv` | Tutorial 2, Task A: the table with one row per file |
| `website/index.html` | **The project website** for presenting: open it in a browser. It shows each step with charts and runs the search engine and classifier live |

---

## 3. What each notebook does, and the key results

### Week 1: building the corpus (`week1_corpus.ipynb`)
- **What:** 32 Wikipedia introductions (8 per topic), saved cleanly with their licence. We run spaCy's French pipeline on them and look at the most frequent words.
- **Key result:** 7,446 tokens, 2,063 different words. The most frequent words are *de, la, et…*: they say nothing about the topic (hence stop words later).
- **Interesting finding:** spaCy splits *l'énergie* correctly into *l'* + *énergie*, but it does not split *du* (= *de + le*), and it does not see *accord de Paris* as one name.

### Week 2: tokenization (`week2_tokenization.ipynb`)
- **What:** we compare three ways of cutting text into tokens (`split()`, NLTK, spaCy) and write our own tokenizer for French with regular expressions.
- **Corpus growth:** the tutorial asks for at least 3 kinds of text, so we added news (Wikinews), discussions (Wikipedia talk pages) and legal texts, not cleaned, as required. The corpus now has **107 texts**.
- **Key results:**
  - **French elisions** (*l'énergie*, *d'émissions*) are the biggest problem. **NLTK does not split them**, even in French mode. spaCy does.
  - Invisible **non-breaking spaces** inside numbers (*1 300*) break every tokenizer.
  - We tokenized sentences by hand (a *gold standard*) to measure precision and recall. Our own tokenizer gets **F1 = 1.00**, spaCy 0.99, NLTK 0.91 and `split()` 0.75 on new test sentences (a small test of 4 sentences, so with care).
  - **N-grams:** *changement → climatique* (87 %), *gaz → à (effet de serre)*. The bigger the n, the rarer each n-gram (sparsity).
  - **Zipf's law holds:** *de* alone is 6.6 % of the corpus, 89 words make up half of all tokens, and the slope is −0.90 (Zipf predicts −1).

### Week 3 / Lab 3: stemming and lemmatization (`week3_lab3_stemming_lemmatization.ipynb`)
- **What:** all the Lab 3 exercises (in English, as given), then the same ideas on our French corpus.
- **Key results (English):**
  - Of the three stemmers, **Snowball** makes the fewest errors (0 over-stemming).
  - **Porter** and **Lancaster** wrongly merge *general/generate* and *communicate/community*.
  - spaCy lemmatizes better than NLTK (97 % vs 91 % on the test text).
  - In WordNet, *coffee* and *tea* are similar (common parent: *beverage*).
- **Key results (French):**
  - Normalization shrinks the vocabulary from 4,890 word forms to 3,266 stems or 3,543 lemmas.
  - Snowball merges more (good for recall) but also over-merges (*important ≈ importation*).
  - spaCy merges verb forms that no stemmer can (*émet, émis → émettre*).
- **Cells that need internet:** the Guardian article and the Hugging Face subwords only run on your laptop. Without internet, the notebook uses our French news texts instead.

### Week 6: POS tagging and stop words (`week6_pos_stopwords.ipynb`)
- **What:** grammatical tags (noun, verb…), ambiguous words, a preprocessing function, stop words and the CoNLL-U format.
- **Key results:**
  - On a real French treebank, **spaCy tags 94.5 %** of the words correctly. The simple baseline gets 85.6 %, our rule-based tagger 79.4 %, and NLTK's English tagger only 32 % (it does not know French).
  - **Ambiguous words** in our texts: *des* (article or *de + les*), *en*, *fait*, *a*, *solaire*…
  - **Stop words are 50 % of all words.** Without them, the top words are *énergie, carbone, gaz, émission*.
  - **Warning:** *"Le charbon **n'est pas** une énergie renouvelable"* becomes the same as *"Le charbon **est** une énergie renouvelable"*, because *ne* and *pas* are stop words. Removing stop words must be a choice that depends on the task.

### The project (`project_search_classification.ipynb`)
- **Search engine:**
  - It turns texts into **TF-IDF** vectors (words frequent in a document but rare elsewhere get a high weight) and ranks the documents by similarity to the query.
  - We tested it on **14 queries** with hand-made relevance judgments. With lemmatization, **Precision@5 = 0.56** (vs 0.47 with plain words), and the first result is almost always relevant (MRR 0.95).
  - It fails when the query uses other words than the documents (*voitures* vs *véhicules*).
- **Classifier:**
  - A linear SVM on TF-IDF features (lemmas + bigrams) gets **macro F1 = 0.84** (accuracy 85 %), against 0.16 for a model that always guesses the biggest class.
  - Most errors are between *emissions* and *climate policy*, which really overlap.
  - Trained only on Wikipedia, it is weaker on news (65 %): a different kind of text is harder.

---

## 4. Words you need to know

| Word | Meaning | Example from our project |
|---|---|---|
| **Corpus** | A collection of texts used for analysis | Our 107 environmental texts |
| **Token** | One piece of text after cutting it: word, number or punctuation mark | *l'*, *énergie*, *9,8*, *%* |
| **Type** | A distinct word form (repeats are counted once) | *de* appears 1,701 times but is 1 type |
| **Tokenizer** | The program that cuts text into tokens | `split()`, NLTK, spaCy, our regex |
| **Elision** | A French article/pronoun that loses its vowel: *le → l'* | *l'énergie*, *qu'il*, *d'émissions* |
| **N-gram** | A sequence of n consecutive words | bigram *gaz à*, trigram *effet de serre* |
| **Zipf's law** | A few words are extremely frequent; most words are rare | *de* = 6.6 % of all tokens |
| **Stemming** | Cutting word endings with rules; the result may not be a word | *énergétique → énerget* |
| **Lemmatization** | Giving the dictionary form; needs the part of speech | *émissions → émission*, *émis → émettre* |
| **Over- / under-stemming** | Merging unrelated words / not merging related ones | *important ≈ importation* / *pollution ≠ polluer* |
| **POS tag** | The grammatical class of a word in its sentence | NOUN, VERB, ADJ, DET, ADP… |
| **Stop words** | Very frequent words with little meaning | *le, de, et, est, pas* |
| **Treebank / CoNLL-U** | A corpus annotated by linguists / its file format, one word per line | UD French-GSD in `data/` |
| **TF-IDF** | A word's weight: frequent in this document, rare in the others | *éolienne* weighs a lot in the wind texts |
| **Precision / Recall** | Of what we returned, how much is right / of what is right, how much we returned | Precision@5, Recall@10 |
| **F1** | One number that combines precision and recall | macro F1 = 0.84 |
| **Baseline** | The simplest possible method, to compare against | "always predict the biggest class" |
| **Cross-validation** | Test on each fifth of the data while training on the other four fifths | 5-fold, stratified |
| **Gold standard** | The correct answers, made by hand | our hand-tokenized sentences |

---

## 5. How to run everything on your laptop

1. Open the folder `french-environmental-nlp` in VS Code.
2. In the VS Code terminal, with your `.venv` active:
   ```bash
   python -m pip install -r requirements.txt
   python -m spacy download fr_core_news_md
   python -m spacy download en_core_web_md      # for Lab 3 (English exercises)
   ```
3. Open a notebook → **Select Kernel** (top right) → choose `.venv` → **Restart** → **Run All**.
4. Optional, for the subword cells (Week 2 section 6 and Lab 3 question 2): `pip install transformers sentencepiece`. They download the tokenizers from Hugging Face the first time.
5. To make the corpus bigger: `python collect_corpus.py --per-category 25` (it adds new texts and never renumbers the old ones).

The notebooks were already run once, so you can read all the results without running anything.

---

## 6. Being honest about the limits

- **The corpus is small** (107 texts, about 33,000 tokens). Good enough for learning and for the project, but the numbers would change with more data.
- **We wrote the relevance judgments and gold standards ourselves.** We did it carefully (the judgments before running the search, the test sentences after writing the tokenizer), but they are small.
- **Some cells need internet** (Guardian article, Hugging Face). Where they could not run, the notebook says so and uses our corpus instead.
- **spaCy makes mistakes too:** *Nations unies → unir*, *Parties → party*, *airpocalypse = adjective*. We point these out instead of hiding them.

---

## 7. What comes next

- **Named entities** (next week): find *ADEME, GIEC, COP21, Pékin, 2050* automatically.
- **Synonyms or word embeddings** to fix *voitures ↔ véhicules* in the search.
- **More news and discussion texts**, and official sources (ADEME, vie-publique.fr, EU) after checking their licences.
- **Multi-label topics** (a text can be about emissions *and* policy).
- A small **web page** where you type a query and see the results.
