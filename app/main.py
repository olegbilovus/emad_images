from typing import List, Annotated

from fastapi import FastAPI, Query

from app.config import settings
from app.control import process_text, find_images_for_keywords
from app.models.images import Sentence, KeywordImages

app = FastAPI(docs_url="/", title=f"NLP API [{settings.language.name}]", version="1.0.0")


@app.get("/health", tags=["health"], summary="Health check", include_in_schema=False)
async def health_check():
    return {"status": "healthy"}


@app.get("/v1/nlp/images/", tags=["nlp/images"], summary="Get images ids and keywords")
def get_images(sentence: Annotated[Sentence, Query()]) -> List[KeywordImages]:
    # Preprocessa la frase
    tokens = process_text(sentence.text)
    # Trova le immagini corrispondenti
    images = find_images_for_keywords(tokens, sentence.sex, sentence.violence, sentence.one_image)

    return images
