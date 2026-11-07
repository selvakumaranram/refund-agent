"""Reading company documents: the 'RAG' part.

Gemini is NOT trained on your policy. Instead, ahead of time we:
  1. read the PDF,  2. cut it into small chunks,  3. turn each chunk into numbers (an "embedding")
and save that as policies/index.json. When a customer asks something, we find the closest chunks and hand
ONLY those to Gemini as context.

No key, or want it free and offline? Use keyword mode (--keyword): same idea, simpler matching.
"""
import json
import math
import re
from collections import Counter
from pathlib import Path
from .config import ROOT

INDEX = ROOT / 'policies/index.json'


def read_pdf(path: Path) -> str:
    from pypdf import PdfReader
    return '\n'.join(page.extract_text() or '' for page in PdfReader(str(path)).pages)


def chunk_policy(text: str) -> list[dict]:
    """One chunk per numbered section ('2. Return window ...'), so each chunk is one complete idea."""
    text = re.sub(r'[ \t]+', ' ', text)
    chunks = []
    for part in re.split(r'\n(?=\d+\.\s+[A-Z])', text):
        first, _, rest = part.strip().partition('\n')
        m = re.match(r'(\d+)\.\s+(.+)', first)
        body = ' '.join(part.split())
        if len(body) < 40:
            continue
        if m:
            chunks.append({'id': f'section-{m.group(1)}', 'title': m.group(2).strip(), 'text': body})
        else:
            chunks.append({'id': 'intro', 'title': first.strip()[:60], 'text': body})
    return chunks


STOP = set(("a an the of to and or for in on is are be it you your we our can if this that with by from not as at "
             "i me my do does have has how what when will would get something please any").split())
SYNONYMS = {'long': 'days window', 'return': 'refund window', 'money': 'refund payment', 'back': 'receive',
            'big': 'large above', 'expensive': 'large above', 'broken': 'damaged', 'voucher': 'gift'}


def _stem(w: str) -> str:
    for suf in ('ing', 'ed', 'es', 's'):
        if w.endswith(suf) and len(w) > len(suf) + 3:
            return w[:-len(suf)]
    return w


def _words(s: str, expand: bool = False) -> list[str]:
    ws = [w for w in re.findall(r'[a-z0-9]+', s.lower()) if w not in STOP]
    if expand:
        ws += ' '.join(SYNONYMS.get(w, '') for w in ws).split()
    return [_stem(w) for w in ws]


def _keyword_scores(query: str, chunks: list[dict]) -> list[float]:
    """BM25, the classic search-engine formula: rare words that appear in a chunk count the most."""
    docs = [Counter(_words(c['title'] + ' ' + c['title'] + ' ' + c['text'])) for c in chunks]   # title counts double
    n, avg = len(docs), sum(sum(d.values()) for d in docs) / len(docs)
    q = set(_words(query, expand=True))
    idf = {w: math.log(1 + (n - sum(1 for d in docs if w in d) + 0.5) / (sum(1 for d in docs if w in d) + 0.5)) for w in q}
    k1, b = 1.5, 0.75
    return [sum(idf[w] * d[w] * (k1 + 1) / (d[w] + k1 * (1 - b + b * sum(d.values()) / avg)) for w in q if d[w]) for d in docs]


def _cos(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)) + 1e-9)


def build_index(pdf: Path, client=None, embed_model: str | None = None) -> dict:
    chunks = chunk_policy(read_pdf(pdf))
    mode = 'keyword'
    if client is not None:
        resp = client.models.embed_content(model=embed_model, contents=[c['text'] for c in chunks])
        for c, e in zip(chunks, resp.embeddings):
            c['embedding'] = list(e.values)
        mode = 'embedding'
    idx = {'source': pdf.name, 'mode': mode, 'model': embed_model if mode == 'embedding' else None, 'chunks': chunks}
    INDEX.write_text(json.dumps(idx))
    return idx


def search(query: str, k: int = 3, client=None) -> list[dict]:
    idx = json.loads(INDEX.read_text())
    chunks = idx['chunks']
    if idx['mode'] == 'embedding' and client is not None:
        q = client.models.embed_content(model=idx['model'], contents=[query]).embeddings[0].values
        scores = [_cos(q, c['embedding']) for c in chunks]
    else:
        scores = _keyword_scores(query, chunks)
    best = sorted(range(len(chunks)), key=lambda i: -scores[i])[:k]
    return [{'section': chunks[i]['id'], 'title': chunks[i]['title'], 'text': chunks[i]['text'], 'score': round(scores[i], 3)} for i in best]
