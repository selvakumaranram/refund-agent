# Step 3: How AI reads your company's documents (RAG)

**You will learn:** how an agent answers from your own documents, and why the AI is **not trained** on them.

## The myth
"We trained Gemini on our refund policy." Almost nobody does that. Training is slow and expensive, and it would
need redoing every time the policy changes.

## What really happens: Retrieval-Augmented Generation (RAG)
**Ahead of time (once, or whenever the PDF changes):**
```
refund-policy.pdf  ->  text  ->  chunks  ->  embeddings  ->  policies/index.json
```
- **Chunks:** small pieces, here one per policy section ("2. Return window ...").
- **Embedding:** a list of numbers that captures what a chunk *means*. Chunks with similar meaning get similar
  numbers, so "How long do I have?" lands near "Return window: 30 days", even with no words in common.

**When a customer asks:**
1. Turn the question into numbers too.
2. Find the 3 closest chunks.
3. Give **only those** to Gemini with the question: "answer from these sections".

```bash
python step-3-policy-search/preprocess.py            # with Gemini embeddings (uses your key)
python step-3-policy-search/preprocess.py --keyword  # free, offline: classic keyword search (BM25)
```

In a real company, the PDF lives in Google Drive or cloud storage and a scheduled job re-runs this step when the
file changes.

## Do you even need RAG?
Our policy is one page. You could simply paste the whole thing into the system instruction on every request,
and for small documents that's often the better choice. RAG matters when you have **many or long** documents
that won't fit, or would cost too much to send every time.

## Try it
```bash
python step-3-policy-search/app.py   # open http://127.0.0.1:8000
```
- "How long do I have to return something?" → `search_policy` returns section 2; the answer cites it.
- "Can I refund a gift card?" → section 3.
- "When will I get my money back?" → section 6.

Open each tool call in **Behind the scenes** to see exactly which text Gemini was given.

## Common mistakes
- **Chunks that are too big or cut mid-sentence.** Split on natural boundaries (sections, headings).
- **Letting the AI answer from memory.** Tell it to answer *only* from the returned sections and to cite them.
- **Using RAG to make decisions.** RAG helps the AI *explain* the policy. Deciding a refund needs exact rules,
  and that's Step 4.

## What's next
The agent knows the orders and the policy. Should it decide refunds? **No.** In **Step 4**, code decides.
