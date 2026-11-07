"""Step 1a: talk to Gemini from Python, twice, and watch it forget.

Run:  python step-1-chat-memory/first_call.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.config import gemini_client, GEMINI_MODEL

client = gemini_client()

# Request 1
r1 = client.models.generate_content(model=GEMINI_MODEL, contents='Hi, this is Kumaran')
print('You:    Hi, this is Kumaran')
print('Gemini:', r1.text)

# Request 2: a brand-new request. Gemini has NO memory of request 1.
r2 = client.models.generate_content(model=GEMINI_MODEL, contents="What's my name?")
print("You:    What's my name?")
print('Gemini:', r2.text)

print('\nThe raw JSON that came back for request 2 (the REST API answers in JSON):')
print(r2.model_dump_json(indent=2, exclude_none=True)[:1500])
