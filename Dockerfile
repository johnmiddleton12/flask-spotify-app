FROM python:3.10-slim

ENV PYTHONUNBUFFERED True

ENV APP_HOME /app
WORKDIR $APP_HOME

COPY ./requirements.txt ./requirements.txt
COPY ./app.py ./app.py
COPY ./templates/index.html ./templates/index.html

RUN pip install --no-cache-dir -r requirements.txt

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
