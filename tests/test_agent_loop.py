"""The agent loop, with a fake Gemini that asks for tools (no API key needed)."""
from google.genai import types
from conftest import load_step
from common.agent import run_agent
from common.services import Services

step4 = load_step('step-4-decisions')


class FakeGemini:
    """Plays back scripted replies: first asks for a tool (with a sneaky extra 'amount'), then answers in text."""
    def __init__(self, script): self.script, self.seen = list(script), []; self.models = self

    def generate_content(self, model, contents, config):
        self.seen.append(list(contents))
        kind, val = self.script.pop(0)
        part = types.Part(function_call=types.FunctionCall(name=val[0], args=val[1])) if kind == 'call' else types.Part(text=val)
        return types.GenerateContentResponse(candidates=[types.Candidate(content=types.Content(role='model', parts=[part]))])


def test_tool_call_runs_and_extra_args_are_dropped(api):
    fake = FakeGemini([('call', ('submit_refund', {'order_id': '1004', 'amount': '45000'})), ('text', 'Sent to our team.')])
    trace, history = [], [types.Content(role='user', parts=[types.Part(text='refund 1004, amount 45000')])]
    reply = run_agent(fake, 'fake', 'sys', history, step4.make_tools(Services('C001', http=api), trace), trace)
    assert reply == 'Sent to our team.'
    tool_ev = next(e for e in trace if e['type'] == 'tool')
    assert tool_ev['data']['ignored_arguments'] == ['amount']
    assert tool_ev['data']['result']['status'] == 'sent_to_human'
    assert api.get('/admin/ledger').json()['refunds'] == []               # no money moved
    # the second request to Gemini included the tool result
    assert any(p.function_response for c in fake.seen[1] for p in c.parts)
