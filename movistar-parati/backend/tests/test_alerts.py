from app.services.change_detection import ALERT_TYPE_LABELS, alert_type_label


def test_alert_type_label():
    assert alert_type_label("monthly_price_drop") == "Si baja la cuota"
    assert alert_type_label("price_drop") == "Si baja de precio"
    assert alert_type_label("unknown") == "unknown"


def test_alert_type_labels_complete():
    assert len(ALERT_TYPE_LABELS) == 3
