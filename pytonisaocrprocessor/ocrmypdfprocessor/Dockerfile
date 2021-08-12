FROM python:3.9

COPY ./pytonisacommons ./pytonisacommons
RUN pip install ./pytonisacommons

COPY ./pytonisaocrprocessor/ocrmypdfprocessor ./pytonisaocrprocessor
WORKDIR /pytonisaocrprocessor

RUN apt-get update && apt-get install ocrmypdf -y
RUN apt-get install tesseract-ocr-por
RUN pip install -r requirements.txt
CMD ["python", "ocrmypdfprocessor.py"]