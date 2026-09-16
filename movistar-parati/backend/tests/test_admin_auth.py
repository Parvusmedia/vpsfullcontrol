from app.services.admin_auth import panel_session_token


def test_panel_session_token_is_stable():
    a = panel_session_token()
    b = panel_session_token()
    assert a == b
    assert len(a) == 64
