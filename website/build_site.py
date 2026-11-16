"""Builds website/index.html: computes the search index, the classifier and the examples from the corpus,
then puts them into website/template.html.  Run from the repository root:  python website/build_site.py
"""
import json, math, re, sys
from collections import Counter, defaultdict
import numpy as np, spacy, nbformat
sys.path.insert(0, '.')
from nlp_utils import load_corpus, preprocess, FR_STOP_WORDS
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import f1_score
from nltk.tokenize import word_tokenize
from nltk.stem.snowball import FrenchStemmer

nlp = spacy.load('fr_core_news_md')
docs = load_corpus()
sd = list(nlp.pipe([d['text'] for d in docs]))
terms = [preprocess(d) for d in sd]
y = [d['category'] for d in docs]

vec = TfidfVectorizer(analyzer=lambda x: x, sublinear_tf=True)
X = vec.fit_transform(terms)
vocab = list(vec.get_feature_names_out()); idf = vec.idf_
clf = LogisticRegression(max_iter=3000, C=10).fit(X, y)
cv = StratifiedKFold(5, shuffle=True, random_state=42)
pred = cross_val_predict(LogisticRegression(max_iter=3000, C=10), X, y, cv=cv)
print('web model (unigram LR) CV macro F1', round(f1_score(y, pred, average='macro'), 3))

# doc vectors (sparse)
dv = []
for i in range(X.shape[0]):
    row = X.getrow(i); dv.append([[int(j), round(float(v), 4)] for j, v in zip(row.indices, row.data)])

# form -> lemma map (only lemmas in vocab)
vset = {w: i for i, w in enumerate(vocab)}
fm = defaultdict(Counter)
for d in sd:
    for t in d:
        if t.is_alpha or '-' in t.text:
            fm[t.lower_][t.lemma_.lower()] += 1
from conllu import parse_incr
for path in ['data/fr_gsd-ud-dev.conllu', 'data/fr_gsd-ud-test.conllu']:
    for s in parse_incr(open(path, encoding='utf-8')):
        for t in s:
            if isinstance(t['id'], int) and t['lemma']:
                fm[t['form'].lower()][t['lemma'].lower()] += 1
formmap = {}
for f, c in fm.items():
    lem = c.most_common(1)[0][0]
    if lem in vset and lem != f:
        formmap[f] = lem
print('vocab', len(vocab), 'formmap', len(formmap))

meta = []
for d in docs:
    txt = re.sub(r'\s+', ' ', d['text']).strip()
    meta.append({'f': d['file'], 't': d['title'], 'k': d['kind'], 'c': d['category'], 'u': d['url'], 'w': int(d['words']),
                 's': txt[:230] + ('…' if len(txt) > 230 else '')})

# Zipf
words = [t.lower_ for d in sd for t in d if t.is_alpha]
freq = Counter(words).most_common()
ranks = sorted(set(list(range(1, 31)) + [int(round(x)) for x in np.logspace(np.log10(31), np.log10(len(freq)), 90)]))
zipf = [[r, freq[r - 1][1], freq[r - 1][0]] for r in ranks if r <= len(freq)]

# tokenizer examples
nb = nbformat.read('week2_tokenization.ipynb', 4)
src = next(c.source for c in nb.cells if c.cell_type == 'code' and 'TOKEN_RE' in c.source)
g = {'re': re}; exec(src.split("print(regex_tokenize")[0], g)
blank = spacy.blank('fr')
sents = ["L'Inde est aujourd'hui le 3ème plus gros émetteur de CO2 du monde derrière la Chine et les États-Unis.",
         "La puissance installée de l'éolien en mer atteint 92 474 MW en 2025, en progression de 11,1 %.",
         "El Comandante (discuter) 11 décembre 2023 à 11:46 (CET)Répondre",
         "Art. 1er. - Chacun a le droit de vivre dans un environnement équilibré et respectueux de la santé.",
         "Ils s'expriment en grammes d'équivalent CO2 par kilowatt-heure (gCO2eq/kWh)."]
tok_ex = [{'s': s, 'split': s.split(), 'nltk': word_tokenize(s, language='french'),
           'spacy': [t.text for t in blank(s) if not t.is_space], 'ours': g['regex_tokenize'](s)} for s in sents]

# hero pipeline
hero = "Le charbon n'est pas une énergie renouvelable : ses émissions de CO2 ont augmenté de 5,8 % en 2023."
hd = nlp(hero)
hero_tokens = [{'x': t.text, 'p': t.pos_, 'l': t.lemma_.lower(), 'stop': bool(t.is_stop or t.lemma_.lower() in FR_STOP_WORDS),
                'drop': bool(t.is_punct or not any(ch.isalpha() for ch in t.text))} for t in hd]
hv = vec.transform([preprocess(hd)])
hp = dict(zip(clf.classes_, clf.predict_proba(hv)[0].round(3).tolist()))
print('hero proba', hp)

# families
st = FrenchStemmer()
fams = {'polluer': ['pollution', 'pollutions', 'polluer', 'polluent', 'pollué', 'polluant', 'polluants', 'pollueur'],
        'émettre': ['émission', 'émissions', 'émettre', 'émet', 'émis', 'émise', 'émetteur'],
        'climat': ['climat', 'climats', 'climatique', 'climatiques'],
        'renouveler': ['renouvelable', 'renouvelables', 'renouveler', 'renouvellement'],
        'importance?': ['important', 'importante', 'importance', 'importation', 'importer']}
def splem(w):
    ctx = {'pollué': "l'air pollué", 'émis': 'le gaz émis', 'émise': 'la chaleur émise', 'émet': 'il émet', 'polluent': 'elles polluent'}
    if w in ctx:
        dd = nlp(ctx[w]); return next(t.lemma_.lower() for t in dd if t.text == w)
    return nlp(w)[0].lemma_.lower()
families = {k: [{'w': w, 'stem': st.stem(w), 'lemma': splem(w)} for w in v] for k, v in fams.items()}

data = {'docs': meta, 'vocab': vocab, 'idf': [round(float(v), 4) for v in idf], 'dv': dv, 'formmap': formmap,
        'stop': sorted(FR_STOP_WORDS), 'classes': list(clf.classes_),
        'coef': [[round(float(v), 3) for v in row] for row in clf.coef_], 'b': [round(float(v), 3) for v in clf.intercept_],
        'zipf': zipf, 'tok': tok_ex, 'hero': {'s': hero, 'tokens': hero_tokens, 'proba': hp}, 'families': families}
s = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
tpl = open('website/template.html', encoding='utf-8').read()
open('website/index.html', 'w', encoding='utf-8').write(tpl.replace('__DATA__', s.replace('</', '<\\/')))
print('website/index.html written,', len(s.encode()) // 1024, 'KB of data')
