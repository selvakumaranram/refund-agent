"""Step 1b: a chat app with MEMORY, plus a system instruction that gives the bot its job.

The Gemini API is stateless: every request is a brand-new chat. The Gemini app only "remembers" because it
re-sends the whole conversation every time. We do the same: keep a list, send the full list.
Flip Memory OFF in the page to see it forget.

Run:  python step-1-chat-memory/app.py      then open http://127.0.0.1:8000
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from google.genai import types
from common.config import gemini_client, GEMINI_MODEL
from common.agent import trim, show
from common.web import make_app, serve

# The SYSTEM INSTRUCTION: the bot's job and rules. Sent with every request, never shown to the customer.
SYSTEM = """You are Asha, the friendly support assistant for ShopKart, an online shop in India.
Keep answers short (2-3 sentences) and warm. Use the customer's name once you know it.
You cannot see orders yet. If someone asks about a specific order, say that you will be able to check orders soon."""
TEMPERATURE = 0.4   # 0 = always the same answer, 1+ = more creative / varied


def chat(session: dict, msg, trace: list) -> str:
    history = session.setdefault('history', [])
    user_turn = types.Content(role='user', parts=[types.Part(text=msg.message)])
    to_send = trim(history + [user_turn]) if msg.memory else [user_turn]     # Memory OFF = only this message

    trace.append({'type': 'sent', 'open': True,
                  'title': f'Sent to Gemini: {len(to_send)} message(s)' + ('' if msg.memory else ' (memory OFF)'),
                  'data': {'system_instruction': SYSTEM, 'temperature': TEMPERATURE, 'contents': show(to_send)}})
    resp = gemini_client().models.generate_content(
        model=GEMINI_MODEL, contents=to_send,
        config=types.GenerateContentConfig(system_instruction=SYSTEM, temperature=TEMPERATURE))
    if msg.memory:
        session['history'] = to_send + [resp.candidates[0].content]
    usage = resp.usage_metadata
    trace.append({'type': 'info', 'title': f'Tokens: {usage.prompt_token_count} in, {usage.candidates_token_count} out',
                  'data': 'More history = more input tokens on every request. That is why we trim old messages.'})
    return resp.text


app = make_app('ShopKart Support Agent', 'Step 1: memory', chat, show_memory_toggle=True)

if __name__ == '__main__':
    serve(app)
