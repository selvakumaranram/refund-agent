"""Policy search in free keyword mode (no API key)."""
from common.config import ROOT
from common.policy_index import build_index, search


def test_finds_the_right_sections():
    build_index(ROOT / 'policies/refund-policy.pdf')
    assert search('Can I refund a gift card?')[0]['section'] == 'section-3'
    assert search('How long do I have to return something?')[0]['section'] == 'section-2'
    assert search('When will I get my money back?')[0]['section'] == 'section-6'
    assert search('refund for a big order over 2000')[0]['section'] == 'section-5'
