"""A tiny web server shared by every step: serves the chat page and passes messages to the step's chat function."""
import uuid
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from . import config

UI = Path(__file__).parent / 'ui/index.html'


class ChatIn(BaseModel):
    session_id: str | None = None
    customer_id: str = 'C001'
    message: str
    memory: bool = True


def make_app(title: str, step: str, chat, show_memory_toggle=False, show_login=False, new_session=dict) -> FastAPI:
    """chat(session: dict, msg: ChatIn, trace: list) -> reply text. `session` is kept per browser tab."""
    app = FastAPI(title=title)
    sessions: dict[str, dict] = {}

    @app.get('/', response_class=HTMLResponse)
    def page():
        return UI.read_text(encoding='utf-8')

    @app.get('/api/info')
    def info():
        return {'title': title, 'step': step, 'memory_toggle': show_memory_toggle, 'login': show_login,
                'model': config.GEMINI_MODEL,
                'customers': [{'id': 'C001', 'name': 'Kumar'}, {'id': 'C002', 'name': 'Priya'}]}

    @app.post('/api/chat')
    def chat_api(msg: ChatIn):
        sid = msg.session_id or uuid.uuid4().hex
        s = sessions.setdefault(sid, new_session())
        if s.get('customer_id') not in (None, msg.customer_id):      # switched login -> start a fresh conversation
            s.clear(); s.update(new_session())
        s['customer_id'] = msg.customer_id
        trace: list = []
        try:
            reply = chat(s, msg, trace)
        except (Exception, SystemExit) as e:                           # show errors (e.g. missing key) in the page
            reply, trace = f'Error: {e}', trace + [{'type': 'error', 'title': type(e).__name__, 'data': str(e)}]
        return {'session_id': sid, 'reply': reply, 'trace': trace}

    @app.post('/api/reset')
    async def reset(req: Request):
        body = await req.json()
        sessions.pop(body.get('session_id'), None)
        return {'ok': True}

    return app


def serve(app: FastAPI):
    import uvicorn
    print(f'\n  Open http://127.0.0.1:{config.APP_PORT} in your browser  (Ctrl+C to stop)\n')
    uvicorn.run(app, host='127.0.0.1', port=config.APP_PORT, log_level='warning')
