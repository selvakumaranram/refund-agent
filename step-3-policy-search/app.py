"""Step 3b: the agent can now READ THE REFUND POLICY.

New tool: search_policy(question). Our code searches policies/index.json and hands Gemini only the
2-3 most relevant sections. Gemini answers from those sections and says which section it used.

Run first:  python step-3-policy-search/preprocess.py   (once)
Then:       python step-3-policy-search/app.py          and open http://127.0.0.1:8000
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from google.genai import types
from common.config import gemini_client, GEMINI_MODEL
from common.agent import run_agent, tool, trim
from common.policy_index import INDEX, search
from common.services import Services, start_mock_api
from common.web import make_app, serve

SYSTEM = """You are Asha, the support assistant for ShopKart, an online shop in India.
- Use get_my_orders / get_order for order facts. Never guess them.
- For ANY question about refunds or returns, call search_policy first and answer ONLY from the sections it returns.
  Mention the section number, e.g. "(policy section 2)". If the sections don't answer it, say you'll connect a human.
- You cannot issue refunds yet. Keep answers short and friendly. Amounts are in rupees (Rs)."""


def make_tools(svc: Services, client=None) -> list:
    def get_my_orders():
        """List the logged-in customer's recent orders."""
        return svc.list_orders()

    @tool(order_id='The order number, for example 1001')
    def get_order(order_id):
        """Get full details of one of the logged-in customer's orders."""
        return svc.get_order(order_id)

    @tool(question='What to look up in the refund policy, in plain words')
    def search_policy(question):
        """Search the official ShopKart refund policy and return the most relevant sections."""
        return {'sections': search(question, k=3, client=client)}

    return [get_my_orders, get_order, search_policy]


def chat(session: dict, msg, trace: list) -> str:
    history = session.setdefault('history', [])
    history.append(types.Content(role='user', parts=[types.Part(text=msg.message)]))
    session['history'] = history = trim(history)
    client = gemini_client()
    return run_agent(client, GEMINI_MODEL, SYSTEM, history, make_tools(Services(msg.customer_id), client), trace)


app = make_app('ShopKart Support Agent', 'Step 3: policy search', chat, show_login=True)

if __name__ == '__main__':
    if not INDEX.exists():
        sys.exit('Run  python step-3-policy-search/preprocess.py  first (it builds policies/index.json).')
    start_mock_api()
    serve(app)
