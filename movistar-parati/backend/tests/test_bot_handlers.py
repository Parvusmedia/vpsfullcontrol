from app.services.bot_commands import BOT_COMMANDS
from app.services.bot_handlers import BTN_OFERTAS, MENU_TEXT, WELCOME_TEXT, _brand_menu, _command_name, _is_casual_greeting


def test_command_name_plain():
    assert _command_name("/ofertas") == "/ofertas"


def test_command_name_with_bot_username():
    assert _command_name("/novedades@Movistarparatibot") == "/novedades"


def test_command_name_with_args():
    assert _command_name("/start demo") == "/start"


def test_command_name_non_command():
    assert _command_name("hola") is None


def test_native_menu_has_menu_command_first():
    assert BOT_COMMANDS[0]["command"] == "start"
    assert BOT_COMMANDS[1]["command"] == "menu"
    commands = {c["command"] for c in BOT_COMMANDS}
    assert {"start", "menu", "ofertas", "moviles", "novedades", "parami", "avisos", "ayuda"} <= commands


def test_casual_greeting_detected():
    assert _is_casual_greeting("Hola")
    assert _is_casual_greeting("buenas!")


def test_reply_button_labels():
    assert BTN_OFERTAS == "🔥 Ofertas"


def test_brand_menu_includes_todos_option():
    keyboard = _brand_menu()
    labels = [btn["text"] for row in keyboard["inline_keyboard"] for btn in row]
    assert "📱 Todos" in labels
    callbacks = [btn["callback_data"] for row in keyboard["inline_keyboard"] for btn in row]
    assert "brand:all" in callbacks


def test_brand_menu_includes_price_filters():
    keyboard = _brand_menu()
    callbacks = [btn["callback_data"] for row in keyboard["inline_keyboard"] for btn in row]
    assert "filter:monthly:10" in callbacks
    assert "filter:monthly:15" in callbacks
    assert "filter:monthly_range:10:20" in callbacks


def test_welcome_text_mentions_precio_and_demo_disclaimer():
    assert "precio" in WELCOME_TEXT.lower()
    assert "concept demo" in WELCOME_TEXT.lower()
    assert "☰" not in WELCOME_TEXT
    assert "Movistar Para Ti" in WELCOME_TEXT
    assert WELCOME_TEXT.index("¡Hola!") < WELCOME_TEXT.index("Bienvenido")


def test_menu_text_is_short():
    assert len(MENU_TEXT) < len(WELCOME_TEXT)
    assert "Menú principal" in MENU_TEXT
