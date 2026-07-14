from fitjourney.auth import hash_password, verify_password


def test_password_roundtrip():
    encoded = hash_password("a careful password")
    assert encoded != "a careful password"
    assert verify_password("a careful password", encoded)
    assert not verify_password("wrong password", encoded)


def test_malformed_hash_fails_closed():
    assert not verify_password("anything", "broken")
