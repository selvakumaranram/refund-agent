import importlib.util
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def load_step(folder: str):
    """Step folders have dashes in their names, so we load them by path."""
    spec = importlib.util.spec_from_file_location(folder.replace('-', '_'), ROOT / folder / 'app.py')
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def api():
    """The mock company APIs, in-process (no server needed), reset for every test."""
    from fastapi.testclient import TestClient
    from mock_services.app import app
    c = TestClient(app); c.post('/admin/reset')
    return c
