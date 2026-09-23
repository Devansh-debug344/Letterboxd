import pytest

from app.models.movie import Movie


@pytest.fixture
async def movie(db):
    m = Movie(
        imdb_id="tt0111161",
        title="The Shawshank Redemption",
        year="1994",
        genre="Drama",
        poster="https://example.com/poster.jpg",
        plot="Two imprisoned men bond over a number of years.",
    )
    db.add(m)
    await db.commit()
    await db.refresh(m)
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


def test_stats_endpoints_hit_cache(client, movie, test_user):
    headers = login_headers(client)

    created = client.post(
        "/api/review/",
        json={"omdb_id": movie.imdb_id, "rating": 4.0, "review": "good"},
        headers=headers,
    )
    assert created.status_code == 201

    user_stats = client.get(f"/api/user/{test_user.id}/stats")
    assert user_stats.status_code == 200
    assert user_stats.json()["reviews"] == 1
    assert user_stats.json()["avg_rating"] == 4.0
    assert user_stats.json()["watchlist"] == 0

    movie_stats = client.get(f"/api/movies/{movie.imdb_id}/stats")
    assert movie_stats.status_code == 200
    assert movie_stats.json()["review_count"] == 1
    assert movie_stats.json()["avg_rating"] == 4.0

    assert client.get(f"/api/user/{test_user.id}/stats").json() == user_stats.json()
    assert client.get(f"/api/movies/{movie.imdb_id}/stats").json() == movie_stats.json()

    deleted = client.request("DELETE", "/api/review/", json={"omdb_id": movie.imdb_id}, headers=headers)
    assert deleted.status_code == 200
    assert client.get(f"/api/user/{test_user.id}/stats").json()["reviews"] == 0
    assert client.get(f"/api/movies/{movie.imdb_id}/stats").json()["review_count"] == 0

def test_movie_detail_serializes_via_pydantic_and_reuses_cache(client, movie):
    first = client.get(f"/api/movies/{movie.imdb_id}")
    assert first.status_code == 200
    body = first.json()
    assert body["title"] == "The Shawshank Redemption"
    assert body["imdb_id"] == movie.imdb_id
    assert body["year"] == 1994

    cached = client.get(f"/api/movies/{movie.imdb_id}")
    assert cached.status_code == 200
    assert cached.json() == body


def test_watchlist_watched_review_lists_are_cached(client, movie, test_user):
    headers = login_headers(client)

    created = client.post(
        "/api/review/",
        json={"omdb_id": movie.imdb_id, "rating": 4.0, "review": "nice"},
        headers=headers,
    )
    assert created.status_code == 201

    wl = client.post("/api/watchlist/", json={"omdb_id": movie.imdb_id}, headers=headers)
    assert wl.status_code == 200

    watchlist_1 = client.get("/api/watchlist/", headers=headers)
    watchlist_2 = client.get("/api/watchlist/", headers=headers)
    assert watchlist_1.status_code == 200
    assert watchlist_2.json() == watchlist_1.json()
    assert watchlist_1.json()["response"][0]["title"] == "The Shawshank Redemption"

    wt = client.post(
        "/api/watched/",
        json={"omdb_id": movie.imdb_id, "rating": 4.0},
        headers=headers,
    )
    assert wt.status_code == 201
    assert client.get("/api/watchlist/", headers=headers).json()["response"] == []

    reviews_1 = client.get("/api/review/", headers=headers)
    reviews_2 = client.get("/api/review/", headers=headers)
    assert reviews_1.status_code == 200
    assert reviews_2.json() == reviews_1.json()
    assert reviews_1.json()[0]["movie_name"] == "The Shawshank Redemption"

    movie_reviews_1 = client.get(f"/api/review/movie/{movie.imdb_id}")
    movie_reviews_2 = client.get(f"/api/review/movie/{movie.imdb_id}")
    assert movie_reviews_2.json() == movie_reviews_1.json()
    assert len(movie_reviews_1.json()) == 1

    watched_1 = client.get("/api/watched/", headers=headers)
    watched_2 = client.get("/api/watched/", headers=headers)
    assert watched_1.status_code == 200
    assert watched_2.json() == watched_1.json()

    deleted = client.request(
        "DELETE", "/api/review/", json={"omdb_id": movie.imdb_id}, headers=headers
    )
    assert deleted.status_code == 200
    assert client.get("/api/review/", headers=headers).json() == []
