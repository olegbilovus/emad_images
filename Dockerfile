FROM python:3.12-slim AS install-dependencies

RUN apt-get update &&  \
    apt-get install -y --no-install-recommends build-essential gcc && \
    apt-get clean && \
    python -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"
ARG SPACY_MODEL="it_core_news_lg"

COPY requirements.txt .
RUN pip install -r requirements.txt && \
    python -m spacy download "${SPACY_MODEL}" && \
    python -m spacy info

FROM python:3.12-slim

COPY --from=install-dependencies /opt/venv /opt/venv

WORKDIR /app

COPY ./app .

ENV JSON_FILE="jsons/it.json"
ENV LANGUAGE="it"

ENV PATH="/opt/venv/bin:$PATH"
CMD ["fastapi", "run", "main.py", "--port", "80"]