FROM python:3.11

WORKDIR /scrapManganatoApi

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY ./app ./app

CMD ["python3" , "./app/main.py"]