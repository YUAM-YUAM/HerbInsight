from src.learning_exercises import EXERCISES, grade_exercise, learning_record
from tests.ui_helpers import open_route


def test_exercise_answers_and_record():
    for section, item in EXERCISES.items():
        for index, option in enumerate(item["options"]):
            assert grade_exercise(section, option) == (index == item["answer"])
        assert not grade_exercise(section, None)
    record = learning_record({"collection": {"attempts": 2, "passed": True, "first_attempt_passed": False}})
    assert len(record["activities"]) == 4
    assert record["activities"][0]["first_attempt_passed"] is False
    assert record["activities"][1]["attempts"] == 0


def test_repair_ui_wrong_then_correct():
    at = open_route("learn_collection")
    at.button(key="repair_submit_collection").click().run()
    assert "repair_records" not in at.session_state
    item = EXERCISES["collection"]
    at.radio(key="repair_choice_collection").set_value(item["options"][0]).run()
    at.button(key="repair_submit_collection").click().run()
    assert not at.session_state["repair_records"]["collection"]["passed"]
    at.radio(key="repair_choice_collection").set_value(item["options"][1]).run()
    at.button(key="repair_submit_collection").click().run()
    result = at.session_state["repair_records"]["collection"]
    assert result["passed"] and result["attempts"] == 2
    assert not result["first_attempt_passed"]
    assert not at.exception


def test_repair_routes_and_resources():
    for route, section in [("learn_enrichment", "enrichment"), ("learn_transcriptome", "transcriptome"), ("learn_ml", "ml")]:
        at = open_route(route)
        item = EXERCISES[section]
        at.radio(key=f"repair_choice_{section}").set_value(item["options"][item["answer"]]).run()
        at.button(key=f"repair_submit_{section}").click().run()
        assert at.session_state["repair_records"][section]["passed"]
        assert not at.exception
    at = open_route("resources")
    assert not at.exception
