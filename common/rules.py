"""THE REFUND DECISION. Plain Python, no AI.

The AI can be persuaded, confused or tricked. This function cannot. It reads the order (from the Order API)
and the rules (policies/rules.json) and returns one of three decisions: refund, deny, or human.
"""
import json
from datetime import date
from .config import ROOT

RULES = json.loads((ROOT / 'policies/rules.json').read_text())


def decide_refund(order: dict, rules: dict = RULES, today: date | None = None) -> dict:
    today = today or date.today()
    checks = []

    def result(decision, amount=0, reason=''):
        return {'order_id': order.get('order_id'), 'decision': decision, 'amount': amount,
                'currency': rules.get('currency', 'INR'), 'reason': reason, 'checks': checks}

    if 'error' in order:
        checks.append({'check': 'Order exists for this customer', 'passed': False, 'detail': order['error']})
        return result('deny', reason='We could not find that order on your account.')
    checks.append({'check': 'Order exists for this customer', 'passed': True, 'detail': order['item']})

    if order.get('status') != 'delivered':
        checks.append({'check': 'Order delivered', 'passed': False, 'detail': order.get('status')})
        return result('deny', reason='This order has not been delivered yet. You can cancel it from the Orders page instead.')
    checks.append({'check': 'Order delivered', 'passed': True, 'detail': order['delivered_on']})

    rule = rules['categories'].get(order.get('category'), rules['default'])
    if not rule.get('refundable'):
        checks.append({'check': 'Category is refundable', 'passed': False, 'detail': order.get('category')})
        return result('deny', reason=rule.get('reason', 'Not refundable.'))
    checks.append({'check': 'Category is refundable', 'passed': True, 'detail': order['category']})

    days = (today - date.fromisoformat(order['delivered_on'])).days
    window = rule['window_days']
    if days > window:
        checks.append({'check': f'Within {window} days of delivery', 'passed': False, 'detail': f'{days} days ago'})
        return result('deny', reason=f'The order was delivered {days} days ago. Refunds are only possible within {window} days.')
    checks.append({'check': f'Within {window} days of delivery', 'passed': True, 'detail': f'{days} days ago'})

    amount = round(order['price'] * rule['refund_percent'] / 100) - order.get('refunded_amount', 0)
    if amount <= 0:
        checks.append({'check': 'Something left to refund', 'passed': False, 'detail': 'already refunded'})
        return result('deny', reason='This order has already been refunded.')
    checks.append({'check': 'Something left to refund', 'passed': True, 'detail': f'Rs {amount}'})

    limit = rules['human_review_above']
    if order.get('open_review_ticket'):
        checks.append({'check': 'No review already open', 'passed': False, 'detail': order['open_review_ticket']})
        return result('human', amount, f'A team member is already reviewing this order (ticket {order["open_review_ticket"]}).')
    if amount > limit:
        checks.append({'check': f'Amount up to Rs {limit}', 'passed': False, 'detail': f'Rs {amount}'})
        return result('human', amount, f'Refunds above Rs {limit} are checked by our team within 24 hours.')
    checks.append({'check': f'Amount up to Rs {limit}', 'passed': True, 'detail': f'Rs {amount}'})
    return result('refund', amount, 'Eligible for a full refund.')
