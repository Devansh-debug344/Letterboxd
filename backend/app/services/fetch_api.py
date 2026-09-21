"""Cached TMDB adapter that returns the legacy OMDb-shaped movie payload."""
from __future__ import annotations
import asyncio
import json
import math
from collections.abc import Awaitable, Callable
from datetime import date
from time import monotonic
from typing import Any

import httpx
from redis import asyncio as redis_async

from app.config import setting

TMDB_API = "https://api.themoviedb.org/3"
POSTER_BASE = "https://image.tmdb.org/t/p/w342"
PROFILE_BASE = "https://image.tmdb.org/t/p/w185"
_CACHE_TTL_SECONDS = 15 * 60
_CACHE_PREFIX = "letterboxd:cache:v1:"
_cache: dict[str, tuple[float, Any]] = {}
_in_flight: dict[str, asyncio.Task[Any]] = {}
_client = httpx.AsyncClient(timeout=httpx.Timeout(8.0, connect=3.0), http2=True)
_redis = redis_async.from_url(setting.REDIS_URL, decode_responses=True) if setting.REDIS_URL else None


def _poster(path: str | None) -> str | None:
    return f"{POSTER_BASE}{path}" if path else None


def _profile(path: str | None) -> str | None:
    return f"{PROFILE_BASE}{path}" if path else None


def _normalise_movie(movie: dict[str, Any], include_details: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {
        "imdbID": str(movie["id"]),  # Existing field name; this is TMDB's ID.
        "Title": movie.get("title"),
        "Year": (movie.get("release_date") or "")[:4] or None,
        "Poster": _poster(movie.get("poster_path")),
        "Plot": movie.get("overview"),
        "imdbRating": str(movie["vote_average"]) if movie.get("vote_average") is not None else None,
        "Type": "movie",
    }
    if include_details:
        credits = movie.get("credits", {})
        trailer = next((video for video in movie.get("videos", {}).get("results", []) if video.get("site") == "YouTube" and video.get("type") in {"Trailer", "Teaser"}), None)
        cast = [{"id": person.get("id"), "name": person.get("name"), "character": person.get("character"), "profile": _profile(person.get("profile_path"))} for person in credits.get("cast", [])[:10]]
        crew_by_person: dict[str, dict[str, Any]] = {}
        role_jobs = {
            "Director": "Director",
            "Writer": "Writer",
            "Screenplay": "Writer",
            "Producer": "Producer",
            "Executive Producer": "Producer",
            "Director of Photography": "Cinematographer",
            "Editor": "Editor",
            "Original Music Composer": "Composer",
        }
        for person in credits.get("crew", []):
            role = role_jobs.get(person.get("job"))
            name = person.get("name")
            if not role or not name:
                continue
            entry = crew_by_person.setdefault(name, {"id": person.get("id"), "name": name, "roles": [], "profile": _profile(person.get("profile_path"))})
            if role not in entry["roles"]:
                entry["roles"].append(role)
        crew = list(crew_by_person.values())[:12]
        result.update({
            "Genre": ", ".join(genre["name"] for genre in movie.get("genres", [])),
            "Runtime": f"{movie['runtime']} min" if movie.get("runtime") else None,
            "Released": movie.get("release_date"),
            "Language": movie.get("original_language"),
            "Tagline": movie.get("tagline"),
            "Actors": ", ".join(person["name"] for person in credits.get("cast", [])[:8]),
            "Director": ", ".join(person["name"] for person in credits.get("crew", []) if person.get("job") == "Director"),
            "Writer": ", ".join(person["name"] for person in credits.get("crew", []) if person.get("department") == "Writing"),
            "cast": cast,
            "crew": crew,
            # Kept for existing clients that use this legacy field.
            "producers": [person for person in crew if "Producer" in person["roles"]][:6],
            "trailer": trailer.get("key") if trailer else None,
        })
    return result


async def _cached(key: str, factory: Callable[[], Awaitable[Any]]) -> Any:
    redis_key = f"{_CACHE_PREFIX}{key}"
    if _redis:
        try:
            cached = await _redis.get(redis_key)
            if cached:
                return json.loads(cached)
        except Exception:
            cached = _cache.get(key)
            if cached and cached[0] > monotonic():
                return cached[1]
    else:
        cached = _cache.get(key)
        if cached and cached[0] > monotonic():
            return cached[1]

    task = _in_flight.get(key)
    if task is None:
        task = asyncio.create_task(factory())
        _in_flight[key] = task
    try:
        value = await task
        if _redis:
            try:
                await _redis.set(redis_key, json.dumps(value), ex=_CACHE_TTL_SECONDS)
            except Exception:
                _cache[key] = (monotonic() + _CACHE_TTL_SECONDS, value)
        else:
            _cache[key] = (monotonic() + _CACHE_TTL_SECONDS, value)
        return value
    finally:
        if task.done():
            _in_flight.pop(key, None)


async def _get(path: str, params: dict[str, str]) -> dict[str, Any]:
    response = await _client.get(f"{TMDB_API}{path}", params={"api_key": setting.tmdb_api_key, **params})
    response.raise_for_status()
    return response.json()


async def fetch_movies_from_api(movie_id: str) -> dict[str, Any]:
    async def request() -> dict[str, Any]:
        return _normalise_movie(await _get(f"/movie/{movie_id}", {"append_to_response": "credits,videos"}), include_details=True)
    return await _cached(f"movie:{movie_id}", request)


async def get_cached_movie(movie_id: str) -> dict[str, Any] | None:
    redis_key = f"{_CACHE_PREFIX}movie:{movie_id}"
    if _redis:
        try:
            cached = await _redis.get(redis_key)
            return json.loads(cached) if cached else None
        except Exception:
            cached = _cache.get(f"movie:{movie_id}")
            return cached[1] if cached and cached[0] > monotonic() else None
    cached = _cache.get(f"movie:{movie_id}")
    return cached[1] if cached and cached[0] > monotonic() else None


async def fetch_movies_from_api_by_search(name: str) -> list[dict[str, Any]]:
    normalised_query = " ".join(name.lower().split())
    async def request() -> list[dict[str, Any]]:
        data = await _get("/search/movie", {"query": name, "include_adult": "false"})
        return [_normalise_movie(movie) for movie in data.get("results", [])]
    return await _cached(f"search:{normalised_query}", request)


async def fetch_person_from_api(person_id: str) -> dict[str, Any]:
    async def request() -> dict[str, Any]:
        person = await _get(f"/person/{person_id}", {"append_to_response": "combined_credits"})
        credits = person.get("combined_credits", {})
        grouped: dict[int, dict[str, Any]] = {}
        for is_cast, credit_list in ((True, credits.get("cast", [])), (False, credits.get("crew", []))):
            for credit in credit_list:
                movie_id = credit.get("id")
                title = credit.get("title") or credit.get("original_title")
                if not movie_id or not title:
                    continue
                entry = grouped.setdefault(movie_id, {
                    "id": movie_id,
                    "imdbID": str(movie_id),
                    "Title": title,
                    "Year": (credit.get("release_date") or "")[:4] or None,
                    "Poster": _poster(credit.get("poster_path")),
                    "imdbRating": str(credit["vote_average"]) if credit.get("vote_average") is not None else None,
                    "popularity": credit.get("popularity") or 0,
                    "vote_count": credit.get("vote_count") or 0,
                    "vote_average": credit.get("vote_average") or 0,
                    "cast_order": credit.get("order", 999),
                    "roles": [],
                    "characters": [],
                })
                if is_cast:
                    if "Acting" not in entry["roles"]:
                        entry["roles"].append("Acting")
                    if credit.get("character") and credit["character"] not in entry["characters"]:
                        entry["characters"].append(credit["character"])
                else:
                    job = credit.get("job")
                    label = {
                        "Director": "Director",
                        "Writer": "Writer",
                        "Screenplay": "Writer",
                        "Producer": "Producer",
                        "Executive Producer": "Producer",
                        "Director of Photography": "Cinematographer",
                        "Editor": "Editor",
                        "Original Music Composer": "Composer",
                    }.get(job, job or "Other")
                    if label not in entry["roles"]:
                        entry["roles"].append(label)
        filmography = sorted(grouped.values(), key=lambda item: item.get("Year") or "", reverse=True)
        current_year = date.today().year

        def known_for_score(credit: dict[str, Any]) -> float:
            year = int(credit["Year"]) if str(credit.get("Year", "")).isdigit() else 0
            role_score = 1.0 if "Acting" not in credit["roles"] else max(0.2, 1 - credit.get("cast_order", 999) / 20)
            recency_score = max(0.0, 1 - abs(current_year - year) / 35) if year else 0.0
            return (
                math.log1p(credit.get("popularity", 0)) * 0.42
                + math.log1p(credit.get("vote_count", 0)) * 0.28
                + min(float(credit.get("vote_average", 0)), 10) * 0.12
                + role_score * 0.13
                + recency_score * 0.05
            )

        known_for = sorted(filmography, key=known_for_score, reverse=True)[:8]
        return {
            "id": person.get("id"),
            "name": person.get("name"),
            "profile": _profile(person.get("profile_path")),
            "known_for_department": person.get("known_for_department"),
            "birthday": person.get("birthday"),
            "place_of_birth": person.get("place_of_birth"),
            "biography": person.get("biography"),
            "filmography": filmography,
            "known_for": known_for,
        }
    return await _cached(f"person:{person_id}", request)


async def fetch_movie_collection(collection: str, page: int = 1) -> dict[str, Any]:
    """Return one TMDB editorial collection, avoiding many title-search calls."""
    async def request() -> dict[str, Any]:
        data = await _get(f"/{collection}/movie/day" if collection == "trending" else f"/movie/{collection}", {"page": str(page)})
        return {"items": [_normalise_movie(movie) for movie in data.get("results", [])], "page": data.get("page", page), "total_pages": data.get("total_pages", page)}
    return await _cached(f"collection:{collection}:{page}", request)
