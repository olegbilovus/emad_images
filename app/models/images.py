from enum import Enum

from pydantic import BaseModel, Field


class Language(str, Enum):
    it = "it"


class ContentFilter(BaseModel):
    sex: bool = Field(False, description="Filter out sexual content")
    violence: bool = Field(False, description="Filter out violent content")


class Sentence(ContentFilter):
    text: str
    language: Language


class Image(BaseModel):
    id: int
    keyword: str
