"""Mock company services: the Order API, the Refund API and the Human-review queue.

In a real company these are existing backend services. The AI agent NEVER touches the database.
It can only call these APIs, and every call says WHO is asking (the X-Customer-Id header, which in a
real app comes from the login token). An API only returns what that customer is allowed to see.

Run on its own:   uvicorn mock_services.app:app --port 8001
(The step apps start it for you in the background.)
"""
import json
from datetime import date, timedelta
from pathlib import Path
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
app = FastAPI(title='ShopKart mock services')

CUSTOMERS = {c['customer_id']: c for c in json.loads((ROOT / 'data/customers.json').read_text())}
_ORDERS = json.loads((ROOT / 'data/orders.json').read_text())
REFUNDS: list[dict] = []         # refunds paid (in memory; resets when the server restarts)
REVIEWS: list[dict] = []         # tickets waiting for a human


def _public(o: dict) -> dict:
    """What the Order API returns: real dates instead of 'days ago', plus how much was already refunded."""
    d = o['delivered_days_ago']
    return {
        'order_id': o['order_id'], 'item': o['item'], 'category': o['category'], 'price': o['price'], 'currency': 'INR',
        'status': o['status'],
        'delivered_on': (date.today() - timedelta(days=d)).isoformat() if d is not None else None,
        'refunded_amount': sum(r['amount'] for r in REFUNDS if r['order_id'] == o['order_id']),
        'open_review_ticket': next((t['ticket_id'] for t in REVIEWS if t['order_id'] == o['order_id']), None),
    }


def _who(x_customer_id: str | None) -> str:
    if not x_customer_id or x_customer_id not in CUSTOMERS:
        raise HTTPException(401, 'Not logged in')
    return x_customer_id


@app.get('/me')
def me(x_customer_id: str | None = Header(None)):
    return CUSTOMERS[_who(x_customer_id)]


@app.get('/orders')
def list_orders(x_customer_id: str | None = Header(None)):
    cid = _who(x_customer_id)
    return {'orders': [_public(o) for o in _ORDERS if o['customer_id'] == cid]}


@app.get('/orders/{order_id}')
def get_order(order_id: str, x_customer_id: str | None = Header(None)):
    cid = _who(x_customer_id)
    o = next((o for o in _ORDERS if o['order_id'] == order_id), None)
    if o is None or o['customer_id'] != cid:          # someone else's order looks exactly like "not found"
        raise HTTPException(404, f'Order {order_id} not found for this account')
    return _public(o)


class RefundIn(BaseModel):
    order_id: str
    amount: int
    reason: str = ''


@app.post('/refunds')
def create_refund(body: RefundIn, x_customer_id: str | None = Header(None)):
    order = get_order(body.order_id, x_customer_id)
    if body.amount <= 0 or body.amount > order['price'] - order['refunded_amount']:
        raise HTTPException(400, 'Refund amount is more than what is left to refund')
    r = {'refund_id': f'R{len(REFUNDS) + 1:04d}', 'order_id': body.order_id, 'customer_id': x_customer_id,
         'amount': body.amount, 'reason': body.reason}
    REFUNDS.append(r)
    return r


class ReviewIn(BaseModel):
    order_id: str
    amount: int
    reason: str = ''


@app.post('/human-review')
def create_review(body: ReviewIn, x_customer_id: str | None = Header(None)):
    order = get_order(body.order_id, x_customer_id)
    if order['open_review_ticket']:
        return {'ticket_id': order['open_review_ticket'], 'already_open': True}
    t = {'ticket_id': f'T{len(REVIEWS) + 1:04d}', 'order_id': body.order_id, 'customer_id': x_customer_id,
         'amount': body.amount, 'reason': body.reason, 'status': 'waiting for a team member'}
    REVIEWS.append(t)
    return t


@app.get('/admin/ledger')
def ledger():
    """For the demo and the attack tests: everything that was refunded or sent to a human."""
    return {'refunds': REFUNDS, 'reviews': REVIEWS}


@app.post('/admin/reset')
def reset():
    REFUNDS.clear(); REVIEWS.clear()
    return {'ok': True}
