FROM python:3.9

ENV POETRY_VERSION "1.1.13"
ENV ENV "prod"

RUN pip install "poetry==$POETRY_VERSION"

COPY ./pytonisacommons ./pytonisacommons
WORKDIR /pytonisa

# Copying just pyproject.toml and poetry.lock in order to cache changes
COPY ./pytonisatelegramclient/pyproject.toml ./
COPY ./pytonisatelegramclient/poetry.lock ./
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi $(test $ENV == prod && echo "--no-dev")

COPY ./pytonisatelegramclient ./

CMD ["poetry", "run", "python", "ocrbot.py"]