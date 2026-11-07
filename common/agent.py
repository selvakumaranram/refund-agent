"""The agent loop: the heart of every AI agent.

    1. Send the conversation + the list of tools to Gemini.
    2. If Gemini answers with text  -> done, show it to the customer.
    3. If Gemini asks to CALL A TOOL -> OUR code runs it (Gemini can't run anything itself),
       we send the JSON result back, and go to step 1.

Gemini only ever *asks*. Your code decides what actually happens.
"""
import inspect
import json
from google.genai import types

MAX_STEPS = 6


def tool(**params):
    """Decorator: @tool(order_id='The order number, for example 1001') adds parameter descriptions."""
    def wrap(fn):
        fn.params = params
        return fn
    return wrap


def declaration(fn) -> types.FunctionDeclaration:
    """Describe a Python function to Gemini: its name, what it does (docstring) and its parameters
    (descriptions come from fn.params = {'order_id': '...'}; see the @tool helper above)."""
    props, required = {}, []
    for name, p in inspect.signature(fn).parameters.items():
        props[name] = {'type': 'string', 'description': getattr(fn, 'params', {}).get(name, name)}
        if p.default is inspect.Parameter.empty:
            required.append(name)
    schema = {'type': 'object', 'properties': props, 'required': required} if props else None
    return types.FunctionDeclaration(name=fn.__name__, description=inspect.getdoc(fn), parameters_json_schema=schema)


def run_agent(client, model: str, system: str, history: list, tools: list, trace: list, temperature: float = 0.2) -> str:
    """history: the conversation so far (list of types.Content). It is updated in place."""
    by_name = {f.__name__: f for f in tools}
    config = types.GenerateContentConfig(
        system_instruction=system,
        temperature=temperature,
        tools=[types.Tool(function_declarations=[declaration(f) for f in tools])] if tools else None,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),  # we run tools ourselves
    )
    for _ in range(MAX_STEPS):
        resp = client.models.generate_content(model=model, contents=history, config=config)
        content = resp.candidates[0].content
        history.append(content)
        calls = resp.function_calls or []
        if not calls:
            return resp.text or ''
        replies = []
        for call in calls:
            fn = by_name.get(call.name)
            allowed = set(inspect.signature(fn).parameters) if fn else set()
            args = {k: str(v) for k, v in (call.args or {}).items() if k in allowed}   # GUARDRAIL: unknown args are dropped
            ignored = sorted(set(call.args or {}) - allowed)
            at = len(trace)                       # so this entry appears before anything the tool itself logs
            try:
                result = fn(**args) if fn else {'error': f'unknown tool {call.name}'}
            except TypeError as e:
                result = {'error': f'bad arguments: {e}'}
            trace.insert(at, {'type': 'tool', 'title': f'Gemini asked: {call.name}({", ".join(f"{k}={v!r}" for k, v in args.items())})',
                          'data': {'arguments': args, **({'ignored_arguments': ignored} if ignored else {}), 'result': result}})
            replies.append(types.Part.from_function_response(name=call.name, response={'result': result}))
        history.append(types.Content(role='user', parts=replies))
    return 'Sorry, I could not finish that. Please try again or ask for a human agent.'


def trim(history: list, keep: int = 24) -> list:
    """Keep the conversation from growing forever (every turn costs tokens). Always cut at a customer message."""
    if len(history) <= keep:
        return history
    cut = history[-keep:]
    while cut and not (cut[0].role == 'user' and cut[0].parts and cut[0].parts[0].text):
        cut = cut[1:]
    return cut


def show(history: list) -> list:
    """A readable copy of what we send to Gemini (for the 'behind the scenes' panel)."""
    out = []
    for c in history:
        for p in c.parts or []:
            if p.text:
                out.append({'role': c.role, 'text': p.text})
            elif p.function_call:
                out.append({'role': 'model', 'tool_call': f'{p.function_call.name}({json.dumps(p.function_call.args)})'})
            elif p.function_response:
                out.append({'role': 'tool', 'tool_result': p.function_response.name})
    return out
