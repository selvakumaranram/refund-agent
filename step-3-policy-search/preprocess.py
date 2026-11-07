"""Step 3a: prepare the company document ONCE, before any customer chats.

  PDF  ->  text  ->  chunks (one per policy section)  ->  embeddings  ->  policies/index.json

In a real company this runs whenever the policy file in Drive / storage changes (a scheduled job).
Gemini is never "trained" on the PDF; we just make it searchable.

Run:  python step-3-policy-search/preprocess.py            (uses Gemini embeddings, needs your key)
      python step-3-policy-search/preprocess.py --keyword  (free, offline keyword search instead)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.config import ROOT, GEMINI_EMBED_MODEL, gemini_client
from common.policy_index import build_index

keyword = '--keyword' in sys.argv
idx = build_index(ROOT / 'policies/refund-policy.pdf',
                  client=None if keyword else gemini_client(), embed_model=GEMINI_EMBED_MODEL)
print(f"Indexed {len(idx['chunks'])} chunks from {idx['source']} ({idx['mode']} mode):")
for c in idx['chunks']:
    dims = f", {len(c['embedding'])} numbers" if 'embedding' in c else ''
    print(f"  {c['id']:<11} {c['title']:<42}{dims}")
print('Saved policies/index.json')
