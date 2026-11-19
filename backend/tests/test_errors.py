from app.keitaro.client import _localize_keitaro_message


def test_offers_permission_message() -> None:
    text = _localize_keitaro_message("You have no permission to access this page - Offers")
    assert "Нет доступа к этому офферу" in text


def test_other_messages_pass_through() -> None:
    assert _localize_keitaro_message("Traffic\\Model\\Offer #1 not found") == "Traffic\\Model\\Offer #1 not found"
