FROM python:3.9

ENV TELEGRAM_API_ID ""
ENV TELEGRAM_API_HASH ""
ENV TELEGRAM_BOT_TOKEN ""
RUN mkdir pytonisa/
WORKDIR /pytonisa
COPY . .
RUN apt-get update && apt-get install ocrmypdf -y
RUN apt-get install tesseract-ocr-por
RUN pip install -r requirements.txt
CMD ["python", "ocr-bot.py"]