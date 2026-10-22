from pathlib import Path
from streamlit.testing.v1 import AppTest


def open_route(route_id):
    at = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=45)
    at.query_params["view"] = route_id
    at.run()
    assert not at.exception
    return at
