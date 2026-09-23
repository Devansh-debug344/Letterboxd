import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from app.schemas.watchlist import CreateSaveMovies, SaveMoviesOut, SaveMoviesUpdate, SaveMoviesDelete
from app.schemas.login import DataToken
from app.models.watchlist import WatchList
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.oauth import get_current_user
from app.db.session import get_db
from app.crud.movie import get_movie_by_omdb_id, save_movie_db
from app.crud.watchlist import create_save_movie, get_watchlist_with_movies, del_save_movie_by_movie_id
from app.services.fetch_api import fetch_movies_from_api
from app.services.rate_limiter import rate_limiter
from app.schemas.movie import MoviesOut
from app.services.cache import invalidate , set_json , get_json
from typing import Union, List

router = APIRouter(
    prefix='/watchlist',
    tags=['Watchlist'],
)


@router.get('/', response_model=dict)
async def handel_get_save_movie(
    current_user: DataToken = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    await rate_limiter.enforce(request, "watchlist:reads", user_id=current_user.id, max_attempts=120, window_seconds=60)
    watchlist_key = f"user:{current_user.id}:watchlist"
    cached = await get_json(watchlist_key)
    if cached is not None:
        return {"user_id": current_user.id, "response": cached}

    watchlist_items = await get_watchlist_with_movies(current_user.id, db)

   

    response = [
        MoviesOut(
            id=movie.id,
            imdb_id=movie.imdb_id,
            title=movie.title,
            genre=movie.genre,
            year=movie.year,
            plot=movie.plot,
            poster=movie.poster,
        )
        for _, movie in watchlist_items
    ]

    await set_json(watchlist_key, response, ttl_seconds=300)

    return {"user_id": current_user.id, "response": response}


@router.post('/', response_model=List[Union[SaveMoviesOut, MoviesOut]])
async def handle_save_movie(
    movie_model: CreateSaveMovies,
    current_user: DataToken = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    await rate_limiter.enforce(request, "watchlist:create", user_id=current_user.id, max_attempts=30, window_seconds=60)
    movie = await get_movie_by_omdb_id(movie_model.omdb_id, db)
    if not movie:
        try:
            movie = await fetch_movies_from_api(movie_model.omdb_id)
        except httpx.HTTPStatusError as error:
            if error.response.status_code == 404:
                raise HTTPException(status_code=404, detail="Movie not found")
            raise HTTPException(status_code=502, detail="Movie service unavailable") from error

        movie = await save_movie_db(movie, db)

    saved_movie = await create_save_movie(movie.id, current_user.id, db)

    if not saved_movie:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Movie not get saved")

    await invalidate(
        f"movie:{movie_model.omdb_id}:stats",
        f"movie:{movie_model.omdb_id}",
        f"user:{current_user.id}:stats",
        f"user:{current_user.id}:watchlist",
    )

    return [
        SaveMoviesOut(movie_id=saved_movie.id, user_id=saved_movie.user_id),
        MoviesOut(
            id=movie.id,
            imdb_id=movie.imdb_id,
            title=movie.title,
            genre=movie.genre,
            year=movie.year,
            plot=movie.plot,
            poster=movie.poster,
        ),
    ]


@router.delete('/')
async def handle_delete_movie(
    movie_model: CreateSaveMovies,
    db: AsyncSession = Depends(get_db),
    current_user: DataToken = Depends(get_current_user),
    request: Request = None,
):
    await rate_limiter.enforce(request, "watchlist:delete", user_id=current_user.id, max_attempts=60, window_seconds=60)
    movie = await get_movie_by_omdb_id(movie_model.omdb_id, db)

    if not movie:
        return {"detail": "Movie was not in watchlist"}

    del_mov = await del_save_movie_by_movie_id(movie.id, current_user.id, db)

    if not del_mov:
        return {"detail": "Movie was not in watchlist"}

    await invalidate(
        f"movie:{movie_model.omdb_id}:stats",
        f"movie:{movie_model.omdb_id}",
        f"user:{current_user.id}:stats",
        f"user:{current_user.id}:watchlist",
    )

    return {"detail": "Movie removed from watchlist successfully"}