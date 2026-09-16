from app.config import Settings


def test_demo_mode_caps_poll_interval():
    settings = Settings(demo_mode=True, poll_interval_seconds=60)
    assert settings.effective_poll_interval_seconds == 15


def test_production_poll_interval_unchanged():
    settings = Settings(demo_mode=False, poll_interval_seconds=60)
    assert settings.effective_poll_interval_seconds == 60
