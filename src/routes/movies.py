import math

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Path
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas import (
    MovieListResponseSchema,
    MovieListItemSchema,
    MovieDetailSchema,
    MovieCreateSchema,
    MovieUpdateSchema,
)

router = APIRouter(prefix="/movies")


@router.get("/", response_model=MovieListResponseSchema)
async def movies_list(
        request: Request,
        page: int = Query(1, ge=1, description="Page number"),
        per_page: int = Query(10, ge=1, le=20, description="Items per page"),
        db: AsyncSession = Depends(get_db),
):
    total_items = int(
        await db.scalar(select(func.count(MovieModel.id)))
    )
    if not total_items:
        raise HTTPException(status_code=404, detail="No movies found.")
    total_pages = math.ceil(total_items / per_page)
    offset = (page - 1) * per_page
    query = (
        select(MovieModel).
        order_by(MovieModel.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    movies = (await db.scalars(query)).all()
    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    base_path = request.url.path.removeprefix("/api/v1")

    prev_page = (
        f"{base_path}?page={page - 1}&per_page={per_page}"
        if page > 1 else None
    )
    next_page = (
        f"{base_path}?page={page + 1}&per_page={per_page}"
        if page < total_pages
        else None
    )
    return MovieListResponseSchema(
        movies=[MovieListItemSchema.model_validate(m) for m in movies],
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )


@router.get(
    "/{movie_id}/",
    response_model=MovieDetailSchema,
    responses={
        404: {"description": "Movie with the given ID was not found."},
    },
)
async def get_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_db),
) -> MovieDetailSchema:
    query = (
        select(MovieModel)
        .options(
            joinedload(MovieModel.actors),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.country),
            joinedload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    movie = await db.scalar(query)
    if movie is None:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found.",
        )
    return MovieDetailSchema.model_validate(movie)


@router.post("/", response_model=MovieDetailSchema, status_code=201)
async def create_movie(movie: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    try:
        existing = await db.execute(
            select(MovieModel).where(
                MovieModel.name == movie.name, MovieModel.date == movie.date
            )
        )
        if existing.scalar():
            raise HTTPException(
                status_code=409,
                detail=(
                    f"A movie with the name '{movie.name}' "
                    f"and release date '{movie.date}' already exists."
                ),
            )

        async def get_or_create(model, **kwargs):
            result = await db.execute(select(model).filter_by(**kwargs))
            instance = result.scalar_one_or_none()
            if instance:
                return instance
            instance = model(**kwargs)
            db.add(instance)
            await db.flush()
            return instance

        country = await get_or_create(
            CountryModel, code=movie.country, name=movie.country
        )
        genres = [await get_or_create(GenreModel, name=genre) for genre in movie.genres]
        actors = [await get_or_create(ActorModel, name=actor) for actor in movie.actors]
        languages = [
            await get_or_create(LanguageModel, name=language)
            for language in movie.languages
        ]
        movie = MovieModel(
            name=movie.name,
            date=movie.date,
            score=movie.score,
            overview=movie.overview,
            status=movie.status,
            budget=movie.budget,
            revenue=movie.revenue,
            country_id=country.id,
        )
        movie.genres.extend(genres)
        movie.actors.extend(actors)
        movie.languages.extend(languages)

        db.add(movie)
        await db.commit()
        await db.refresh(movie)
        await db.refresh(
            movie, attribute_names=["country", "genres", "actors", "languages"]
        )
        return movie
    except IntegrityError:
        await db.rollback()

        raise HTTPException(
            status_code=400,
            detail="Invalid input data.",
        )


@router.delete("/{movie_id}/", status_code=204)
async def delete_movie(
        movie_id: int = Path(ge=1, description="ID of the movie to delete"),
        db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()

    if movie is None:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    await db.delete(movie)
    await db.commit()


@router.patch("/{movie_id}/")
async def update_movie(
        movie_id: int, movie_data: MovieUpdateSchema, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )

    update_data = movie_data.model_dump(exclude_unset=True)

    try:
        if "score" in update_data and not (0 <= update_data["score"] <= 100):
            raise ValueError("Score must be between 0 and 100")
        if "budget" in update_data and update_data["budget"] < 0:
            raise ValueError("Budget must be non-negative")
        if "revenue" in update_data and update_data["revenue"] < 0:
            raise ValueError("Revenue must be non-negative")
    except Exception:
        raise HTTPException(
            status_code=404, detail="Invalid input data."
        )

    for field, value in update_data.items():
        setattr(movie, field, value)

    await db.commit()

    return {"detail": "Movie updated successfully."}
