# Build a Refund Agent with the Gemini API, step by step

A customer-support AI agent for a pretend online shop, **ShopKart**. Customers chat with it, it looks up their
orders, reads the refund policy, and then refunds the order, says no, or hands it to a human.

You build it in 5 small steps. Each step is a folder that runs on its own, and each one has a `TUTORIAL.md`
written for beginners.

| Step | Folder | You learn | Video |
|---|---|---|---|
| 1 | `step-1-chat-memory` | Call Gemini with an API key, why the API forgets you, how to add memory, how to control answers | Episode 1 |
| 2 | `step-2-tools` | Give the AI data **without** giving it your database: tools / function calling | Episode 2 |
| 3 | `step-3-policy-search` | Let the AI read company PDFs (RAG): chunks, embeddings, search | Episode 3 |
| 4 | `step-4-decisions` | **The AI talks, the code decides**: refund / deny / human | Episode 4 |
| 5 | `step-5-attacks` | Try to trick your own agent (prompt injection) and prove it holds | Episode 5 |

## The whole system in one picture

```
Customer ──► Chat page ──► Your backend (agent loop) ◄──► Gemini
                              │      Gemini only ASKS for a tool. Your code runs it.
                              ▼
                     Tools (plain Python + guardrails)
     get_my_orders  get_order  search_policy  check_refund  submit_refund
           │            │           │              │              │
       Order API    Order API   policy index   rules.py      Refund API / Human queue
```

Three rules this project follows (and teaches):
1. **The AI never touches the database.** It can only call a few tools, and each tool calls an API.
2. **Who the customer is comes from the login, never from the chat.** Typing "I am Kumar" changes nothing.
3. **Money decisions are code, not AI.** No tool has an `amount` parameter. `common/rules.py` decides.

## Setup (about 3 minutes)

You need Python 3.10 or newer.

```bash
# 1. Install
cd refund-agent
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Add your free API key
cp .env.example .env               # Windows: copy .env.example .env
#    open .env and paste your key from https://aistudio.google.com/apikey

# 3. Run step 1
python step-1-chat-memory/app.py   # then open http://127.0.0.1:8000
```

Every step runs the same way: `python step-N-.../app.py`, then open http://127.0.0.1:8000.
Steps 3 to 5 need the policy index once: `python step-3-policy-search/preprocess.py`
(add `--keyword` to do it free and offline).

## Check everything works without an API key

```bash
pytest
```
21 tests check the rules, the APIs, the guardrails and the agent loop using a fake Gemini. No key, no cost.

## What's inside

```
common/            shared code: agent loop, rules, policy search, API client, web page
mock_services/     pretend company APIs: orders, refunds, human-review queue (FastAPI)
data/              sample customers and orders
policies/          refund-policy.pdf (the document) + rules.json (the same rules, for code)
step-1 ... step-5  one folder per episode, each with a TUTORIAL.md
tests/             automatic checks (run with: pytest)
```

**Sample orders** (logged in as Kumar, C001):

| Order | Item | Price | Delivered | What should happen |
|---|---|---|---|---|
| 1001 | Cotton T-shirt | Rs 799 | 10 days ago | Refund |
| 1002 | Wireless headphones | Rs 2,499 | 40 days ago | Deny (past 30 days) |
| 1003 | Gift card | Rs 1,000 | 2 days ago | Deny (not refundable) |
| 1004 | Smartphone | Rs 45,000 | 5 days ago | Human review (over Rs 2,000) |
| 1005 | Running shoes | Rs 1,899 | not delivered | Deny (cancel instead) |
| 2001 | Silk saree (Priya's order) | Rs 3,200 | 3 days ago | Kumar can't even see it |

Dates are calculated from today, so the examples always behave the same way.

## Notes
- Model names change over time. If you get a "model not found" error, set `GEMINI_MODEL` in `.env`
  to a current model from https://ai.google.dev/gemini-api/docs/models
- The free tier has rate limits. If you see a 429 error, wait a minute and try again.
- Never put your API key in frontend code or commit `.env`.
