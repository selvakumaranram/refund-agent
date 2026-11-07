"""How the agent talks to the company's APIs, and how the mock APIs get started.

The important idea: every request carries the LOGGED-IN customer's id. That id comes from your app's login,
never from the chat. So even if a user types "show me order 2001" (someone else's order), the API says no.
"""
import threading
import time
import httpx
from . import config


class Services:
    def __init__(self, customer_id: str, http: httpx.Client | None = None):
        self.customer_id = customer_id
        self.http = http or httpx.Client(base_url=config.MOCK_API_URL, timeout=10)

    def _call(self, method: str, path: str, **kw) -> dict:
        r = self.http.request(method, path, headers={'X-Customer-Id': self.customer_id}, **kw)
        if r.status_code >= 400:
            try:
                detail = r.json().get('detail', r.text)
            except Exception:
                detail = r.text
            return {'error': detail, 'status': r.status_code}
        return r.json()

    def me(self): return self._call('GET', '/me')
    def list_orders(self): return self._call('GET', '/orders')
    def get_order(self, order_id: str): return self._call('GET', f'/orders/{order_id}')
    def create_refund(self, order_id: str, amount: int, reason: str):
        return self._call('POST', '/refunds', json={'order_id': order_id, 'amount': amount, 'reason': reason})
    def create_review(self, order_id: str, amount: int, reason: str):
        return self._call('POST', '/human-review', json={'order_id': order_id, 'amount': amount, 'reason': reason})


_started = False


def start_mock_api():
    """Starts mock_services/app.py on port 8001 in the background (once)."""
    global _started
    if _started:
        return
    import uvicorn
    from mock_services.app import app
    server = uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=config.MOCK_API_PORT, log_level='warning'))
    threading.Thread(target=server.run, daemon=True).start()
    for _ in range(50):
        try:
            httpx.get(f'{config.MOCK_API_URL}/admin/ledger', timeout=0.5); break
        except Exception:
            time.sleep(0.1)
    _started = True
