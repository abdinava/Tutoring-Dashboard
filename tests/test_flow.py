from tutoring_kiosk.flow import CLASSES, CONFIRM, HOME, MESSAGE, Flow
from tutoring_kiosk.rcard import Card

CARD = Card("999999901", "Pat Tester")


def new_flow():
    saved = []
    return Flow(saved.extend, "ula-pi-01"), saved


def test_swipe_checkin_saves_one_event_per_class():
    flow, saved = new_flow()
    flow.swipe(CARD)
    assert flow.state.screen == CONFIRM
    flow.confirm(True)
    flow.toggle("CS 10A")
    flow.toggle("CS 61")
    assert flow.finish()
    assert flow.state.screen == MESSAGE
    assert [e["course"] for e in saved] == ["CS 10A", "CS 61"]
    assert all(e["method"] == "swipe" and e["timestamp"].endswith("+00:00") for e in saved)


def test_cannot_finish_without_a_class():
    flow, saved = new_flow()
    flow.swipe(CARD)
    flow.confirm(True)
    flow.toggle("CS 10A")
    flow.toggle("CS 10A")  # unselect
    assert not flow.finish()
    assert flow.state.screen == CLASSES and saved == []


def test_bad_card_and_not_me_save_nothing():
    flow, saved = new_flow()
    flow.swipe(None)
    assert flow.state.screen == MESSAGE
    flow.reset()
    flow.swipe(CARD)
    flow.confirm(False)
    assert flow.state.screen == MESSAGE and saved == []


def test_manual_entry():
    flow, saved = new_flow()
    flow.start_manual()
    assert not flow.enter_id("12345")
    assert flow.enter_id("999999901")
    flow.toggle("CS 100")
    flow.finish()
    assert saved[0]["method"] == "manual"


def test_reset_clears_student_info():
    flow, _ = new_flow()
    flow.swipe(CARD)
    flow.reset()
    assert flow.state.screen == HOME and flow.state.name is None
