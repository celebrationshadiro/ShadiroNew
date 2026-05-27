from canonical_models.common import UserRole
from core.security import create_access_token, create_refresh_token, decode_access_token, decode_refresh_token


def test_access_token_contract():
    token = create_access_token("usr_test", UserRole.CUSTOMER)
    payload = decode_access_token(token)

    assert payload["sub"] == "usr_test"
    assert payload["role"] == "customer"
    assert payload["token_type"] == "access"
    assert payload["jti"]


def test_refresh_token_contract():
    token, raw_payload = create_refresh_token("usr_test", UserRole.VENDOR)
    payload = decode_refresh_token(token)

    assert payload["sub"] == "usr_test"
    assert payload["role"] == "vendor"
    assert payload["token_type"] == "refresh"
    assert payload["family_id"] == raw_payload["family_id"]
