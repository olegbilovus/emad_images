from pydantic import BaseModel, Field


class ContentFilter(BaseModel):
    sex: bool = Field(False, description="Filter out sexual content")
    violence: bool = Field(False, description="Filter out violent content")


class Sentence(ContentFilter):
    text: str
    one_image: bool = Field(True, description="Return only one image per keyword")


class Image(ContentFilter):
    id: int


class KeywordImages(BaseModel):
    keyword: str
    images: list[Image]
