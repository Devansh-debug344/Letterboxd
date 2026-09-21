import pytest

from app.models.movie import Movie


@pytest.fixture
def movie(db):
    m = Movie(
        imdb_id="tt0111161",
        title="The Shawshank Redemption",
        year="1994",
        genre="Drama",
        poster="https://example.com/poster.jpg",
        plot="Two imprisoned men bond over a number of years.",
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


def login_headers(client) -> dict:
    response = client.post(
        "/api/login",
        data={"username": "testuser", "password": "testpass123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_create_review_is_idempotent(client, movie, test_user):
    headers = login_headers(client)

    first = client.post(
        "/api/review/",
        json={"omdb_id": movie.imdb_id, "rating": 4.5, "review": "great"},
        headers=headers,
    )
    assert first.status_code == 201
    assert first.json()["rating"] == 4.5

    duplicate = client.post(
        "/api/review/",
        json={"omdb_id": movie.imdb_id, "rating": 1.5, "review": "overwrite?"},
        headers=headers,
    )
    assert duplicate.status_code == 201
    assert duplicate.json()["rating"] == 4.5
    assert duplicate.json()["review"] == "great"


def test_watchlist_add_duplicate_and_list(client, movie, test_user):
    headers = login_headers(client)

    added = client.post("/api/watchlist/", json={"omdb_id": movie.imdb_id}, headers=headers)
    assert added.status_code == 200

    duplicate = client.post("/api/watchlist/", json={"omdb_id": movie.imdb_id}, headers=headers)
    assert duplicate.status_code == 200

    listing = client.get("/api/watchlist/", headers=headers)
    assert listing.status_code == 200
    body = listing.json()
    assert body["user_id"] == listing.json()["user_id"]
    assert len(body["response"]) == 1
    assert body["response"][0]["imdb_id"] == movie.imdb_id


def test_watched_moves_movie_out_of_watchlist(client, movie, test_user):
    headers = login_headers(client)

    assert client.post("/api/watchlist/", json={"omdb_id": movie.imdb_id}, headers=headers).status_code == 200

    watched = client.post(
        "/api/watched/",
        json={"omdb_id": movie.imdb_id, "rating": 5.0},
        headers=headers,
    )
    assert watched.status_code == 201

    watchlist = client.get("/api/watchlist/", headers=headers).json()["response"]
    assert watchlist == []

    listing = client.get("/api/watched/", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    removed = client.delete(f"/api/watched/{movie.imdb_id}", headers=headers)
    assert removed.status_code == 200
    assert client.get("/api/watched/", headers=headers).json() == []