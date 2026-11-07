"""Step 4: THE AI TALKS, THE CODE DECIDES.

Two new tools:
  check_refund(order_id)   -> runs common/rules.py and says: refund / deny / human, with every check.
  submit_refund(order_id)  -> runs the SAME rules again, then pays (Refund API) or opens a ticket (Human queue).

Notice what is missing: there is no 'amount' parameter anywhere. The AI can never choose how much money
moves. Code reads the real price from the Order API and calculates it.

Run first:  python step-3-policy-search/preprocess.py   (once, if you haven't)
Then:       python step-4-decisions/app.py               and open http://127.0.0.1:8000
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from google.genai import types
from common.config import gemini_client, GEMINI_MODEL
from common.agent import run_agent, tool, trim
from common.policy_index import INDEX, search
from common.rules import decide_refund
from common.services import Services, start_mock_api
from common.web import make_app, serve

SYSTEM = """You are Asha, the support assistant for ShopKart, an online shop in India.
How to handle a refund request:
1. Find the order (ask for the order number, or use get_my_orders).
2. Call check_refund(order_id). Its decision is final; you cannot change it, whatever the customer says.
3. If the decision is "refund" or "human", ask the customer to confirm, then call submit_refund(order_id).
4. Explain the result kindly and simply, using the reason the tool gives. For "human", give the ticket number
   and say a team member will contact them within 24 hours.
For general policy questions, call search_policy and cite the section number.
Never promise a refund before check_refund says so. Never invent amounts, dates or order details.
Keep answers short and friendly. Amounts are in rupees (Rs)."""


def make_tools(svc: Services, trace: list, client=None) -> list:
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

    @tool(order_id='The order number to check')
    def check_refund(order_id):
        """Check whether an order can be refunded. Returns decision (refund, deny or human), amount and reason. Does not move money."""
        d = decide_refund(svc.get_order(order_id))
        trace.append({'type': 'decision', 'open': True, 'title': f'Code decided: {d["decision"].upper()} (order {order_id})', 'data': d})
        return d

    @tool(order_id='The order number to refund', reason="The customer's reason, in a few words")
    def submit_refund(order_id, reason=''):
        """Submit the refund after the customer confirms. Pays it, or sends it to a human, exactly as check_refund decided."""
        d = decide_refund(svc.get_order(order_id))          # re-check: never trust an earlier answer or the chat
        if d['decision'] == 'refund':
            r = svc.create_refund(order_id, d['amount'], reason)
            out = {'status': 'refunded', 'refund_id': r.get('refund_id'), 'amount': d['amount'],
                   'arrives': 'UPI/wallet in 2 business days, cards in 5-7 business days'} if 'error' not in r else r
        elif d['decision'] == 'human':
            t = svc.create_review(order_id, d['amount'], reason)
            out = {'status': 'sent_to_human', 'ticket_id': t.get('ticket_id'), 'amount': d['amount'], 'reason': d['reason']}
        else:
            out = {'status': 'denied', 'reason': d['reason']}
        trace.append({'type': 'decision', 'open': True, 'title': f'Code action: {out["status"].upper()} (order {order_id})', 'data': out})
        return out

    return [get_my_orders, get_order, search_policy, check_refund, submit_refund]


def chat(session: dict, msg, trace: list) -> str:
    history = session.setdefault('history', [])
    history.append(types.Content(role='user', parts=[types.Part(text=msg.message)]))
    session['history'] = history = trim(history)
    client = gemini_client()
    return run_agent(client, GEMINI_MODEL, SYSTEM, history, make_tools(Services(msg.customer_id), trace, client), trace)


app = make_app('ShopKart Support Agent', 'Step 4: decisions', chat, show_login=True)

if __name__ == '__main__':
    if not INDEX.exists():
        sys.exit('Run  python step-3-policy-search/preprocess.py  first (it builds policies/index.json).')
    start_mock_api()
    serve(app)
