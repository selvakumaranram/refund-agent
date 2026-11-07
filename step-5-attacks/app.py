"""Step 5: try to break your own agent.

This is the Step 4 agent, unchanged. The page now shows attack messages as quick buttons.
Click them and watch the 'Behind the scenes' panel: the AI may be fooled into ASKING for a refund,
but the code check says no, every time.

Run:  python step-5-attacks/app.py      then open http://127.0.0.1:8000
Automated version:  python step-5-attacks/red_team.py
"""
import importlib.util
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from common.policy_index import INDEX
from common.services import start_mock_api
from common.web import make_app, serve

spec = importlib.util.spec_from_file_location('step4', ROOT / 'step-4-decisions/app.py')
step4 = importlib.util.module_from_spec(spec); spec.loader.exec_module(step4)

app = make_app('ShopKart Support Agent', 'Step 5: attacks', step4.chat, show_login=True)

if __name__ == '__main__':
    if not INDEX.exists():
        sys.exit('Run  python step-3-policy-search/preprocess.py  first (it builds policies/index.json).')
    start_mock_api()
    serve(app)
