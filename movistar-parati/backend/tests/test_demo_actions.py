from app.services.demo_actions import demo_actions_for_product


def test_demo_actions_pixel():
    actions = demo_actions_for_product("pixel-11-256", 12)
    assert len(actions) == 1
    assert actions[0]["new_monthly"] == 8


def test_demo_actions_generic_fallback():
    actions = demo_actions_for_product("unknown-phone", 10.0)
    assert len(actions) == 1
    assert actions[0]["new_monthly"] == 8.0
