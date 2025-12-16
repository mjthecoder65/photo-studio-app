FROM python:3.13

RUN apt-get update
RUN pip install --upgrade pip
RUN pip install poetry

WORKDIR /app

RUN useradd -m -s /bin/bash appuser

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false
RUN poetry install --no-root 

COPY . .

EXPOSE 8080