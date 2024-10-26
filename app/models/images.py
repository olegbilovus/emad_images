from enum import Enum

from pydantic import BaseModel, Field


class Language(str, Enum):
    it = "it"


class ContentFilter(BaseModel):
    sex: bool = Field(True, description="Sexual content")
    violence: bool = Field(True, description="Violent content")


class Sentence(ContentFilter):
    text: str
    language: Language


class Image(BaseModel):
    id: int
    keyword: str
