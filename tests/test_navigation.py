"""Direct navigation, deep links and project persistence."""
from src.navigation import NAV_GROUPS, ROUTES, COURSE_ORDER, resolve_route, course_neighbors
from tests.ui_helpers import open_route


def test_route_registry():
    ids = [entry[0] for entries in NAV_GROUPS.values() for entry in entries]
    assert len(ids) == len(set(ids))
    assert set(COURSE_ORDER) <= set(ROUTES)
    assert resolve_route("unknown") == "home"
    assert resolve_route(None) == "home"
    assert course_neighbors("learn_home") == (None, "learn_collection")
    assert course_neighbors("resources") == ("learn_perturbation", None)
    assert course_neighbors("case_home") == (None, None)


def test_direct_navigation_and_project_persistence():
    at = open_route("learn_home")
    assert not at.sidebar.radio
    assert at.session_state["active_project"] == "wujisan_uc"
    selector = at.selectbox(key="active_project")
    chosen = selector.options[0]
    selector.set_value(chosen).run()
    at.button(key="nav_learn_ml").click().run()
    assert not at.exception
    assert at.query_params["view"] == "learn_ml"
    assert at.session_state["active_project"] == chosen
    at.button(key="course_next").click().run()
    assert at.query_params["view"] == "learn_immune"
    at.button(key="course_previous").click().run()
    assert at.query_params["view"] == "learn_ml"
    at.button(key="nav_learn_home").click().run()
    assert not at.exception
    assert at.session_state["active_project"] == chosen


def test_deep_link_and_invalid_route():
    at = open_route("learn_disease")
    assert at.query_params["view"] in ("learn_disease", ["learn_disease"])
    assert not any(button.key == "start_learn_collection" for button in at.button)
    invalid = open_route("invalid-route")
    assert any(button.key == "home_start_demo" for button in invalid.button)
