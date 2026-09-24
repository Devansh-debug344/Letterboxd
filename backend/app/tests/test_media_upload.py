import pytest


def _auth_headers(client) -> dict:
    response = client.post(
        "/api/login",
        data={"username": "testuser", "password": "testpass123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_avatar_upload_requires_auth(client, test_user):
    response = client.post("/api/user/avatar", files={"file": ("a.png", b"x", "image/png")})
    assert response.status_code == 401


def test_avatar_upload_stores_secure_url(client, test_user, monkeypatch):
    headers = _auth_headers(client)

    call = {"n": 0}

    def fake_upload(*a, **k):
        call["n"] += 1
        suffix = "abc123" if call["n"] == 1 else "new456"
        return {
            "public_id": f"letterboxd/avatars/user_1/avatar/{suffix}",
            "secure_url": f"https://res.cloudinary.com/demo/image/upload/v1/letterboxd/avatars/user_1/avatar/{suffix}.png",
            "url": f"http://res.cloudinary.com/demo/image/upload/v1/letterboxd/avatars/user_1/avatar/{suffix}.png",
            "format": "png",
            "width": 512,
            "height": 512,
            "bytes": 1234,
        }

    monkeypatch.setattr("app.api.user.cloudinary_configured", lambda: True)
    monkeypatch.setattr("app.api.user.upload_image", fake_upload)
    deleted: list[str] = []
    monkeypatch.setattr("app.api.user.delete_image", lambda public_id: deleted.append(public_id))

    response = client.post(
        "/api/user/avatar",
        files={"file": ("avatar.png", b"\x89PNG\r\n\x1a\npretend-bytes", "image/png")},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["avatar_url"] == "https://res.cloudinary.com/demo/image/upload/v1/letterboxd/avatars/user_1/avatar/abc123.png"

    profile = client.get("/api/user/profile", headers=headers)
    assert profile.status_code == 200
    assert profile.json()["avatar_url"] == "https://res.cloudinary.com/demo/image/upload/v1/letterboxd/avatars/user_1/avatar/abc123.png"

    client.post(
        "/api/user/avatar",
        files={"file": ("new.png", b"new-bytes", "image/png")},
        headers=headers,
    )
    assert "letterboxd/avatars/user_1/avatar/abc123" in deleted


def test_avatar_upload_validates_type_and_size(client, test_user, monkeypatch):
    headers = _auth_headers(client)
    monkeypatch.setattr("app.api.user.cloudinary_configured", lambda: True)

    bad_type = client.post(
        "/api/user/avatar",
        files={"file": ("evil.txt", b"hello", "text/plain")},
        headers=headers,
    )
    assert bad_type.status_code == 415

    oversized = client.post(
        "/api/user/avatar",
        files={"file": ("big.png", b"0" * (5 * 1024 * 1024 + 1), "image/png")},
        headers=headers,
    )
    assert oversized.status_code == 413


def test_media_upload_returns_asset_metadata(client, test_user, monkeypatch):
    headers = _auth_headers(client)

    fake_asset = {
        "public_id": "letterboxd/uploads/user_1/media/abc456",
        "secure_url": "https://res.cloudinary.com/demo/image/upload/v1/letterboxd/uploads/user_1/media/abc456.jpg",
        "url": "http://res.cloudinary.com/demo/image/upload/v1/letterboxd/uploads/user_1/media/abc456.jpg",
        "format": "jpg",
        "width": 800,
        "height": 600,
        "bytes": 2048,
    }
    monkeypatch.setattr("app.api.media.cloudinary_configured", lambda: True)
    monkeypatch.setattr("app.api.media.upload_image", lambda *a, **k: fake_asset)

    response = client.post(
        "/api/media/upload",
        files={"file": ("photo.jpg", b"jpeg-bytes", "image/jpeg")},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["secure_url"] == fake_asset["secure_url"]
    assert response.json()["public_id"] == fake_asset["public_id"]

    assert client.post(
        "/api/media/upload",
        files={"file": ("photo.gif", b"gif", "image/gif")},
        headers=headers,
    ).status_code == 200


def test_media_upload_unavailable_when_not_configured(client, test_user, monkeypatch):
    headers = _auth_headers(client)
    monkeypatch.setattr("app.api.media.cloudinary_configured", lambda: False)

    response = client.post(
        "/api/media/upload",
        files={"file": ("photo.jpg", b"jpeg-bytes", "image/jpeg")},
        headers=headers,
    )
    assert response.status_code == 503