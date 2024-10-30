import json
import random
import re
from typing import List

import pymongo
import spacy

from app.config import settings, STOP_WORDS_ALL, PRONOUMS_ALL, SPACY_MODELS
from app.models.images import Image

nlp = spacy.load(SPACY_MODELS[settings.language])
print(spacy.info())
print(f"Loaded model: {SPACY_MODELS[settings.language]}")

DATABASE_NAME = settings.mongodb_database
COLLECTION_NAME = settings.mongodb_collection

db = pymongo.MongoClient(settings.mongodb_uri,
                         connectTimeoutMS=1000,
                         socketTimeoutMS=1000,
                         timeoutms=500
                         )[DATABASE_NAME]

with open(settings.json_file, 'r', encoding="utf8") as f:
    jsonData = json.load(f)

STOP_WORDS = STOP_WORDS_ALL[settings.language]


# Funzione per tokenizzare la frase, rimuovere le stopwords e aggiungere pronomi impliciti
# noinspection t
def process_text(text: str):
    p_text = re.sub(r"[,.]", " ", text)
    p_text = re.sub(r"\s+", " ", p_text).strip().lower()
    doc = nlp(p_text)
    # Rimuoviamo le parole indesiderate dalla ricerca immagine
    filtered_tokens = [token for token in doc if token.text not in STOP_WORDS]

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


PRONOUMS = PRONOUMS_ALL[settings.language]


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

    # If the first search fails, use the file as a fallback for all the other searches in the same request
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


MONGODB_LANG_KEYWORD = f'keywords.{settings.language.name}.keyword'
MONGODB_LANG_PLURAL = f'keywords.{settings.language.name}.plural'


def db_find_images_from_word(word, sex_flag, violence_flag) -> List[Image]:
    sex = {"sex": False} if sex_flag else {}
    violence = {"violence": False} if violence_flag else {}
    images = db[COLLECTION_NAME].find(
        # dict1 | dict2  will merge the dictionaries
        {"$or": [{MONGODB_LANG_KEYWORD: word}, {MONGODB_LANG_PLURAL: word}]} | sex | violence,
        {"_id": 1, "sex": 1, "violence": 1})  # project to return only the _id field

    return [Image(id=image["_id"], keyword=word, sex=image["sex"], violence=image["violence"]) for image in images]


def file_find_images_from_word(word, sex_flag, violence_flag) -> List[Image]:
    matching_images = []

    for image in jsonData:
        if image["sex"] and sex_flag or image["violence"] and violence_flag:
            continue
        for keyword in image["keywords"]:
            if word == keyword["keyword"] or word == keyword.get("plural", ""):
                matching_images.append(Image(id=image["_id"],
                                             keyword=word, sex=image["sex"],
                                             violence=image["violence"]))
                break

    return matching_images
