"""The APIs only show a customer their own data."""

def test_list_only_my_orders(api):
    ids = [o['order_id'] for o in api.get('/orders', headers={'X-Customer-Id': 'C001'}).json()['orders']]
    assert ids == ['1001', '1002', '1003', '1004', '1005']

def test_someone_elses_order_is_not_found(api):
    assert api.get('/orders/2001', headers={'X-Customer-Id': 'C001'}).status_code == 404

def test_not_logged_in(api):
    assert api.get('/orders').status_code == 401

def test_refund_cannot_exceed_price(api):
    r = api.post('/refunds', json={'order_id': '1001', 'amount': 50000}, headers={'X-Customer-Id': 'C001'})
    assert r.status_code == 400
