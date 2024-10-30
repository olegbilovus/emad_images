from pydantic import BaseModel, Field


class ContentFilter(BaseModel):
    sex: bool = Field(False, description="Filter out sexual content")
    violence: bool = Field(False, description="Filter out violent content")


class Sentence(ContentFilter):
    text: str


class Image(ContentFilter):
    id: int
    keyword: str
