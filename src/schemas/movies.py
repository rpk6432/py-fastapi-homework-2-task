from pydantic import BaseModel, ConfigDict, Field, field_validator
import datetime as dt

from database.models import MovieStatusEnum


class BasicMovieModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str = Field(max_length=255)
    date: dt.date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: dt.date) -> dt.date:
        if value > dt.date.today() + dt.timedelta(days=365):
            raise ValueError
        return value


class CountrySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str = Field(pattern=r"^[A-Z]{3}$")
    name: str | None


class GenreSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class ActorSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class LanguageSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class MovieDetailSchema(BasicMovieModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    country: CountrySchema
    genres: list[GenreSchema]
    actors: list[ActorSchema]
    languages: list[LanguageSchema]


class MovieCreateSchema(BasicMovieModel):
    model_config = ConfigDict(from_attributes=True)
    country: str = Field(pattern=r"^[A-Z]{3}$")
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MovieListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    date: dt.date
    score: float
    overview: str


class MovieListResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    movies: list[MovieListItemSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class MovieUpdateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str | None = Field(default=None, max_length=255)
    date: dt.date | None = None
    score: float | None = Field(default=None, ge=0, le=100)
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: float | None = Field(default=None, ge=0)
    revenue: float | None = Field(default=None, ge=0)

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: dt.date | None) -> dt.date | None:
        if value and value > dt.date.today() + dt.timedelta(days=365):
            raise ValueError
        return value
