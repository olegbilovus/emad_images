FROM condaforge/mambaforge:24.9.2-0 AS conda

COPY environment.yml .
RUN conda env create --prefix /opt/venv -f environment.yml

ENV PATH="/opt/venv/bin:$PATH"
ARG SPACY_MODEL="it_core_news_lg"

RUN python -m spacy download "${SPACY_MODEL}" && \
    python -m spacy info

FROM python:3.11-slim

RUN useradd -m app && \
    apt-get update &&  \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean

USER app

COPY --from=conda /opt/venv /opt/venv

WORKDIR /app

COPY ./app .

HEALTHCHECK --interval=10s --timeout=3s \
    CMD curl -s --fail http://127.0.0.1:80/health || exit 1

ENV JSON_FILE="jsons/it.json"
ENV LANGUAGE="it"

ENV PATH="/opt/venv/bin:$PATH"
CMD ["fastapi", "run", "main.py", "--port", "80"]