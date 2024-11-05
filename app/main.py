from typing import List, Annotated

from fastapi import FastAPI, Query

from app.config import settings
from app.control import process_text, find_images_for_keywords
from app.models.images import Sentence, Image

app = FastAPI(docs_url="/", title=f"NLP API [{settings.language.name}]", version="1.0.0")


@app.get("/v1/nlp/images/", tags=["nlp/images"], summary="Get images ids and keywords")
def get_images(sentence: Annotated[Sentence, Query()]) -> List[Image]:
    corrected_text = correct_text_contextual(sentence.text)
    tokens = process_text(corrected_text)  # Preprocessa la frase
    images = find_images_for_keywords(tokens, sentence.sex, sentence.violence)  # Trova le immagini corrispondenti

    return images
