FROM python:3.9

ENV POETRY_VERSION "1.1.13"
ENV ENV "prod"

RUN apt-get update && apt-get install ocrmypdf -y
RUN apt-get install tesseract-ocr-por

RUN pip install "poetry==$POETRY_VERSION"

COPY ./pytonisacommons ./pytonisacommons
WORKDIR /pytonisaocrprocessor/ocrmypdfprocessor

# Copying just pyproject.toml and poetry.lock in order to cache changes
COPY ./pytonisaocrprocessor/ocrmypdfprocessor/pyproject.toml ./
COPY ./pytonisaocrprocessor/ocrmypdfprocessor/poetry.lock ./
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi $(test $ENV == prod && echo "--no-dev")

COPY ./pytonisaocrprocessor/ocrmypdfprocessor ./

CMD ["poetry", "run", "python", "ocrmypdfprocessor.py"]