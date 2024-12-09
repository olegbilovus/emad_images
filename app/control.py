import json
import random
import re
from typing import List

import pymongo
import spacy

from app.config import settings, STOP_WORDS_ALL, PRONOUMS_ALL, SPACY_MODELS
from app.models.images import KeywordImages, Image

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
    global_subject_found = False  # Indica se è stato trovato un soggetto esplicito nella frase

    # Passo 1: Identifica se esiste un soggetto esplicito in tutta la frase
    for token in filtered_tokens:
        if token.dep_ in ["nsubj", "nsubj:pass"] and token.pos_ in ["NOUN", "PROPN", "PRON"]:
            global_subject_found = True
            break  # Non serve continuare, abbiamo trovato un soggetto esplicito

    # Passo 2: Elabora i token e aggiungi pronomi impliciti solo se necessario
    for token in filtered_tokens:
        # Aggiungi il token ai final_tokens
        if token.pos_ not in "PRON" or token.text not in [t.text for t in final_tokens]:
            final_tokens.append(token)

        # Gestione dei verbi
        if token.pos_ in ["VERB", "AUX"]:
            # Controlla se il verbo ha un soggetto nelle sue dipendenze
            has_subject_in_dependencies = any(
                child.dep_ in ["nsubj", "nsubj:pass"] and child.pos_ in ["NOUN", "PROPN", "PRON"]
                for child in token.children
            )
            # Se il soggetto è trovato globalmente o nelle dipendenze, non aggiungere un pronome implicito
            if global_subject_found or has_subject_in_dependencies:
                continue
            # Se non c'è un soggetto esplicito, aggiungi il pronome implicito
            pronoun = get_pronoun_from_verb(token)
            if pronoun:
                pronoun_token = nlp(pronoun)[0]
                if pronoun_token.text not in [t.text for t in final_tokens]:
                    final_tokens.append(pronoun_token)

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
def find_images_for_keywords(tokens, sex_flag, violence_flag, one_image=True) -> List[KeywordImages]:
    images = []

    # If the first search fails, use the file as a fallback for all the other searches in the same request
    use_file = False
    for token in tokens:
        # Cerca immagini per la parola originale
        token_images, use_file = find_images_from_word_failover(token.text, sex_flag, violence_flag, use_file)

        # Se non trovi immagini, prova con la lemmatizzazione
        if not token_images.images:
            lemma_word = token.lemma_

            # Controlla se il lemma contiene uno spazio
            lemma_token = lemma_word.split()[0]  # Separa il lemma in più token

            token_images, use_file = find_images_from_word_failover(lemma_token, sex_flag, violence_flag, use_file)

        if token_images.images:
            if one_image:
                token_images.images = [random.choice(token_images.images)]

            images.append(token_images)
        else:
            images.append(KeywordImages(keyword=token.text, images=[]))

    return images


def find_images_from_word_failover(word, sex_flag, violence_flag, use_file=False) -> (KeywordImages, bool):
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


def db_find_images_from_word(word, sex_flag, violence_flag) -> KeywordImages:
    sex = {"sex": False} if sex_flag else {}
    violence = {"violence": False} if violence_flag else {}
    images = db[COLLECTION_NAME].find(
        # dict1 | dict2 will merge the dictionaries
        {"$or": [{MONGODB_LANG_KEYWORD: word}, {MONGODB_LANG_PLURAL: word}]} | sex | violence,
        {"_id": 1, "sex": 1, "violence": 1})  # project to return only the necessary fields

    keyword_images = KeywordImages(keyword=word, images=[])
    if images:
        keyword_images.images = [Image(id=image["_id"], sex=image["sex"], violence=image["violence"]) for image in
                                 images]

    return keyword_images


def file_find_images_from_word(word, sex_flag, violence_flag) -> KeywordImages:
    keyword_images = KeywordImages(keyword=word, images=[])

    for image in jsonData:
        if image["sex"] and sex_flag or image["violence"] and violence_flag:
            continue
        for keyword in image["keywords"]:
            if word == keyword["keyword"] or word == keyword.get("plural", ""):
                keyword_images.images.append(Image(id=image["_id"],
                                                   sex=image["sex"],
                                                   violence=image["violence"]))
                break

    return keyword_images
