FROM python:3.9

# install pytonisacommons
COPY ./pytonisacommons ./pytonisacommons
RUN pip install ./pytonisacommons

COPY ./pytonisatelegramclient ./pytonisa
WORKDIR /pytonisa

RUN pip install -r requirements.txt
CMD ["python", "ocrbot.py"]