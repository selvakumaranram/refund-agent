"""Step 1c: control the SHAPE of the answer.

Instead of free text, we tell Gemini: "reply only with JSON that looks exactly like this".
Your code can then read the answer reliably (no guessing what the sentence means).

Run:  python step-1-chat-memory/structured_output.py
"""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from google.genai import types
from common.config import gemini_client, GEMINI_MODEL

client = gemini_client()

SCHEMA = {
    'type': 'object',
    'properties': {
        'intent':   {'type': 'string', 'enum': ['refund', 'order_status', 'question', 'other']},
        'order_id': {'type': 'string', 'description': 'Order number if the customer mentioned one, else empty'},
        'mood':     {'type': 'string', 'enum': ['happy', 'neutral', 'upset']},
    },
    'required': ['intent', 'order_id', 'mood'],
}

message = 'This is the second time my T-shirt from order 1001 came torn. I want my money back!'
resp = client.models.generate_content(
    model=GEMINI_MODEL,
    contents=message,
    config=types.GenerateContentConfig(
        system_instruction='You classify customer messages for a shop.',
        temperature=0,                         # 0 = same answer every time (good for classification)
        response_mime_type='application/json', # reply with JSON only
        response_json_schema=SCHEMA,           # ...in exactly this shape
    ),
)
data = json.loads(resp.text)
print('Customer:', message)
print('Gemini returned JSON:', json.dumps(data, indent=2))
print('\nNow plain code can act on it:', 'route to refund flow' if data['intent'] == 'refund' else 'answer normally')
