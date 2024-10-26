from typing import List, Annotated

from fastapi import FastAPI, Query

from app.control import process_text, find_images_for_keywords
from app.models.images import Sentence, Image

app = FastAPI(docs_url="/", title="NLP API", version="1.0.0")


@app.get("/v1/nlp/images/", tags=["nlp/images"], summary="Get images ids and keywords")
def get_images(sentence: Annotated[Sentence, Query()]) -> List[Image]:
    tokens = process_text(sentence.text)  # Preprocessa la frase
    images = find_images_for_keywords(tokens, sentence.sex, sentence.violence)  # Trova le immagini corrispondenti

    return images
