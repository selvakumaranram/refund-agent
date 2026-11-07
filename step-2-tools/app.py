"""Step 2: give the agent DATA, safely, through tools (function calling).

We never give the AI the database. Instead we give it a short menu of tools. Each tool is a normal Python
function that calls a company API and returns JSON. Gemini can only ASK for a tool; our code runs it.

The customer id is NOT a tool parameter. It comes from the login (the dropdown in the page), so the AI
cannot look up someone else's orders even if the user asks it to.

Run:  python step-2-tools/app.py      then open http://127.0.0.1:8000
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from google.genai import types
from common.config import gemini_client, GEMINI_MODEL
from common.agent import run_agent, tool, trim
from common.services import Services, start_mock_api
from common.web import make_app, serve

SYSTEM = """You are Asha, the support assistant for ShopKart, an online shop in India.
Use the tools to look up the customer's orders. Never guess order details; if a tool returns an error, say so politely.
Amounts are in Indian rupees (Rs). Keep answers short and friendly.
You cannot issue refunds yet; if asked, say refunds are coming soon."""


def make_tools(svc: Services) -> list:
    """The ONLY things the AI can do. Each returns JSON from an API."""

    def get_my_orders():
        """List the logged-in customer's recent orders (order number, item, price, status, delivery date)."""
        return svc.list_orders()

    @tool(order_id='The order number, for example 1001')
    def get_order(order_id):
        """Get full details of one of the logged-in customer's orders."""
        return svc.get_order(order_id)

    return [get_my_orders, get_order]


def chat(session: dict, msg, trace: list) -> str:
    history = session.setdefault('history', [])
    history.append(types.Content(role='user', parts=[types.Part(text=msg.message)]))
    session['history'] = history = trim(history)
    trace.append({'type': 'info', 'title': f'Logged in as {msg.customer_id} (sent in the X-Customer-Id header, not by the AI)',
                  'data': {'tools_available': ['get_my_orders()', 'get_order(order_id)']}})
    return run_agent(gemini_client(), GEMINI_MODEL, SYSTEM, history, make_tools(Services(msg.customer_id)), trace)


app = make_app('ShopKart Support Agent', 'Step 2: tools', chat, show_login=True)

if __name__ == '__main__':
    start_mock_api()
    serve(app)
