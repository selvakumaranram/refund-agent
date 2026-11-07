"""The refund decision is plain code, so we can test every case exactly."""
from datetime import date, timedelta
from common.rules import decide_refund

TODAY = date(2026, 11, 7)


def order(category='apparel', price=799, days=10, status='delivered', refunded=0, ticket=None):
    return {'order_id': 'X', 'item': 'thing', 'category': category, 'price': price, 'status': status,
            'delivered_on': (TODAY - timedelta(days=days)).isoformat() if days is not None else None,
            'refunded_amount': refunded, 'open_review_ticket': ticket}


def test_small_recent_order_is_refunded():
    d = decide_refund(order(), today=TODAY)
    assert d['decision'] == 'refund' and d['amount'] == 799

def test_outside_30_days_is_denied():
    assert decide_refund(order('electronics', 2499, days=40), today=TODAY)['decision'] == 'deny'

def test_day_30_is_still_allowed():
    assert decide_refund(order(days=30), today=TODAY)['decision'] == 'refund'

def test_gift_card_is_never_refundable():
    assert decide_refund(order('gift_card', 1000, days=2), today=TODAY)['decision'] == 'deny'

def test_big_amount_goes_to_a_human():
    d = decide_refund(order('electronics', 45000, days=5), today=TODAY)
    assert d['decision'] == 'human' and d['amount'] == 45000

def test_exactly_2000_is_automatic():
    assert decide_refund(order(price=2000), today=TODAY)['decision'] == 'refund'

def test_not_delivered_is_denied():
    assert decide_refund(order(status='shipped', days=None), today=TODAY)['decision'] == 'deny'

def test_already_refunded_is_denied():
    assert decide_refund(order(refunded=799), today=TODAY)['decision'] == 'deny'

def test_unknown_category_is_denied():
    assert decide_refund(order('furniture'), today=TODAY)['decision'] == 'deny'

def test_order_not_found_is_denied():
    assert decide_refund({'error': 'not found'}, today=TODAY)['decision'] == 'deny'
