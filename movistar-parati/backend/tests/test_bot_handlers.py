from app.services.bot_handlers import _command_name


def test_command_name_plain():
    assert _command_name("/ofertas") == "/ofertas"


def test_command_name_with_bot_username():
    assert _command_name("/novedades@Movistarparatibot") == "/novedades"


def test_command_name_with_args():
    assert _command_name("/start demo") == "/start"


def test_command_name_non_command():
    assert _command_name("hola") is None
