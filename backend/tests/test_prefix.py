from app.services.campaigns import with_campaign_prefix


def test_adds_ukolov_prefix() -> None:
    assert with_campaign_prefix("campaign1", "test_ukolov_") == "test_ukolov_campaign1"


def test_does_not_double_prefix() -> None:
    assert with_campaign_prefix("test_ukolov_campaign1", "test_ukolov_") == "test_ukolov_campaign1"
