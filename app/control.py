import json
import random
import re
from typing import List

import pymongo
import spacy

from app.config import settings
from app.models.images import Image

nlp = spacy.load("it_core_news_lg")
print(spacy.info())

ARTICLES = ['a', 'e', 'gli', 'i', 'il', 'l', "l'", 'la', 'le', 'lo', 'si']

DATABASE_NAME = settings.mongodb_database
COLLECTION_NAME = settings.mongodb_collection

db = pymongo.MongoClient(settings.mongodb_uri,
                         connectTimeoutMS=1000,
                         socketTimeoutMS=1000,
                         timeoutms=500
                         )[DATABASE_NAME]

with open(settings.json_file, 'r', encoding="utf8") as f:
    jsonData = json.load(f)


# Funzione per tokenizzare la frase, rimuovere le stopwords e aggiungere pronomi impliciti
# noinspection t
def process_text(text: str):
    p_text = re.sub(r"[,'.]", " ", text)
    p_text = re.sub(r"\s+", " ", p_text).strip().lower()
    doc = nlp(p_text)
    # Rimuoviamo gli articoli dalle parole di ricerca immagine
    filtered_tokens = [token for token in doc if token.text not in ARTICLES]

    final_tokens = []
    pronoun_found = False

    for token in filtered_tokens:
        # Aggiungi un pronome solamente se non già presente
        if token.pos_ != "PRON" or token.text not in [t.text for t in final_tokens]:
            final_tokens.append(token)

        if (token.pos_ == "PRON" and token.morph.get("PronType") == ["Prs"]) or (token.pos_ in ["NOUN", "PROPN"]):
            pronoun_found = True

        if token.pos_ in ["VERB", "AUX"]:
            if not pronoun_found:
                pronoun = get_pronoun_from_verb(token)
                if pronoun:
                    pronoun_token = nlp(pronoun)[0]
                    # Aggiungi il pronome solo se non è già presente
                    if pronoun_token.text not in [t.text for t in final_tokens]:
                        final_tokens.append(pronoun_token)
            pronoun_found = False

    return final_tokens


PRONOUMS = {
    "1Sing": "io",
    "2Sing": "tu",
    "3Sing": "lui/lei",
    "1Plur": "noi",
    "2Plur": "voi",
    "3Plur": "loro"
}


# Funzione per determinare il pronome soggetto dal verbo coniugato
def get_pronoun_from_verb(verb_token):
    if verb_token.morph.get("Person") and verb_token.morph.get("Number"):
        person = verb_token.morph.get("Person")[0]
        number = verb_token.morph.get("Number")[0]
        key = person + number

        return PRONOUMS.get(key)


# Funzione per trovare immagini corrispondenti alle parole chiave, considerando il plurale
def find_images_for_keywords(tokens, sex_flag, violence_flag) -> List[Image]:
    images = []
    use_file = False
    for token in tokens:
        # Cerca immagini per la parola originale
        token_images, use_file = find_images_from_word_failover(token.text, sex_flag, violence_flag, use_file)

        # Se non trovi immagini, prova con la lemmatizzazione
        if not token_images:
            lemma_word = token.lemma_

            # Controlla se il lemma contiene uno spazio
            lemma_token = lemma_word.split()[0]  # Separa il lemma in più token

            token_images, use_file = find_images_from_word_failover(lemma_token, sex_flag, violence_flag, use_file)

        if token_images:
            # Se ci sono immagini corrispondenti, scegli casualmente per ciascuna parola
            images.append(random.choice(token_images))

    return images


def find_images_from_word_failover(word, sex_flag, violence_flag, use_file=False) -> (List[Image], bool):
    try:
        if not use_file:
            return db_find_images_from_word(word, sex_flag, violence_flag), False
        if use_file:
            raise Exception("Forced file usage")
    except Exception as e:
        print(e)
        return file_find_images_from_word(word, sex_flag, violence_flag), True


def db_find_images_from_word(word, sex_flag, violence_flag) -> List[Image]:
    sex = {"sex": False} if sex_flag else {}
    violence = {"violence": False} if violence_flag else {}
    images = db[COLLECTION_NAME].find(
        # dict1 | dict2  will merge the dictionaries
        {"$or": [{"keywords.keyword": word}, {"keywords.plural": word}]} | sex | violence,
        {"_id": 1})  # project to return only the _id field

    return [Image(id=image["_id"], keyword=word) for image in images]


def file_find_images_from_word(word, sex_flag, violence_flag) -> List[Image]:
    matching_images = []

    for pictogram in jsonData:
        if pictogram["sex"] and sex_flag or pictogram["violence"] and violence_flag:
            continue
        for keyword in pictogram["keywords"]:
            if word == keyword["keyword"] or word == keyword.get("plural", ""):
                matching_images.append(Image(id=pictogram["_id"], keyword=word))
                break

    return matching_images
