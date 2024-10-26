from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongodb_uri: str
    mongodb_database: str
    mongodb_collection: str
    json_file: str


settings = Settings()
