"""Call the Step 4 tools directly, the way a tricked AI might, and check the money ledger."""
from conftest import load_step
from common.agent import declaration
from common.services import Services

step4 = load_step('step-4-decisions')


def tools(api, cid='C001'):
    trace = []
    return {f.__name__: f for f in step4.make_tools(Services(cid, http=api), trace)}


def test_no_tool_lets_the_ai_choose_an_amount(api):
    for f in tools(api).values():
        schema = declaration(f).parameters_json_schema or {'properties': {}}
        assert 'amount' not in schema['properties'], f.__name__

def test_small_refund_is_paid_once(api):
    t = tools(api)
    assert t['submit_refund']('1001', 'torn')['status'] == 'refunded'
    assert t['submit_refund']('1001', 'again')['status'] == 'denied'          # no double refund
    assert sum(r['amount'] for r in api.get('/admin/ledger').json()['refunds']) == 799

def test_phone_goes_to_human_not_paid(api):
    assert tools(api)['submit_refund']('1004', 'changed mind')['status'] == 'sent_to_human'
    led = api.get('/admin/ledger').json()
    assert led['refunds'] == [] and led['reviews'][0]['order_id'] == '1004'

def test_old_order_and_gift_card_denied(api):
    t = tools(api)
    assert t['submit_refund']('1002')['status'] == 'denied'
    assert t['submit_refund']('1003')['status'] == 'denied'
    assert api.get('/admin/ledger').json()['refunds'] == []

def test_cannot_refund_someone_elses_order(api):
    assert tools(api, 'C001')['submit_refund']('2001')['status'] == 'denied'
    assert tools(api, 'C002')['submit_refund']('1001')['status'] == 'denied'
    assert api.get('/admin/ledger').json()['refunds'] == []
