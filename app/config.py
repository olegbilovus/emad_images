from enum import Enum

from pydantic_settings import BaseSettings


class Language(str, Enum):
    it = "it"
    en = "en"


class Settings(BaseSettings):
    mongodb_uri: str
    mongodb_database: str
    mongodb_collection: str
    json_file: str
    language: Language


settings = Settings()

SPACY_MODELS = {
    "it": "it_core_news_lg",
    "en": "en_core_web_lg"
}

STOP_WORDS_ALL = {
    "it": ['a', 'e', 'gli', 'i', 'il', 'l', "l'", 'la', 'le', 'lo', 'si'],
    "en": ['a', 'an', 'the']
}

PRONOUMS_ALL = {
    "it": {
        "1Sing": "io",
        "2Sing": "tu",
        "3Sing": "lui/lei",
        "1Plur": "noi",
        "2Plur": "voi",
        "3Plur": "loro"
    },
    "en": {
        "1Sing": "I",
        "2Sing": "you",
        "3Sing": "he/she",
        "1Plur": "we",
        "2Plur": "you",
        "3Plur": "they"
    }
}
