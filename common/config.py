"""Settings, read from the .env file in the project folder."""
import os
from functools import lru_cache
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env')

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '').strip()
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-3.8-flash').strip()
GEMINI_EMBED_MODEL = os.getenv('GEMINI_EMBED_MODEL', 'gemini-embedding-001').strip()
MOCK_API_PORT = int(os.getenv('MOCK_API_PORT', '8001'))
MOCK_API_URL = os.getenv('MOCK_API_URL', f'http://127.0.0.1:{MOCK_API_PORT}')
APP_PORT = int(os.getenv('APP_PORT', '8000'))


@lru_cache(maxsize=1)
def gemini_client():
    """The one object that talks to Gemini. It sends your API key in a header on every request."""
    if not GEMINI_API_KEY:
        raise SystemExit('\n  No API key found.\n  1. Get a free key at https://aistudio.google.com/apikey\n'
                         '  2. Copy .env.example to .env and paste the key after GEMINI_API_KEY=\n')
    from google import genai
    return genai.Client(api_key=GEMINI_API_KEY)
