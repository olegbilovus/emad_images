FROM python:3.12-slim AS install-dependencies

RUN apt-get update &&  \
    apt-get install -y --no-install-recommends build-essential gcc && \
    apt-get clean && \
    python -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"
ARG SPACY_MODEL="it_core_news_lg"
ARG MBART_MODEL="MRNH/mbart-italian-grammar-corrector"

COPY requirements.txt .
RUN pip install -r requirements.txt

RUN python -m spacy download "${SPACY_MODEL}" && \
    python -m spacy info

RUN huggingface-cli download "${MBART_MODEL}" --force-download && \
    huggingface-cli scan-cache

FROM python:3.12-slim

COPY --from=install-dependencies /opt/venv /opt/venv
COPY --from=install-dependencies /root/.cache/huggingface /root/.cache/huggingface

WORKDIR /app

COPY ./app .

ENV JSON_FILE="jsons/it.json"
ENV LANGUAGE="it"

ENV PATH="/opt/venv/bin:$PATH"
CMD ["fastapi", "run", "main.py", "--port", "80"]