FROM python:3.9

ARG TELEGRAM_API_ID
ARG TELEGRAM_API_HASH
ARG TELEGRAM_BOT_TOKEN
RUN TELEGRAM_API_ID=$TELEGRAM_API_ID
RUN TELEGRAM_API_HASH=$TELEGRAM_API_HASH
RUN TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN
RUN mkdir pytonisa/
WORKDIR /pytonisa
COPY . .
RUN apt-get update && apt-get install ocrmypdf -y
RUN apt-get install tesseract-ocr-por
RUN pip install -r requirements.txt
CMD ["python", "ocr-bot.py"]