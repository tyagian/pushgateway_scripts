FROM python:3.9.10-alpine3.14

LABEL Maintainer="AnujTyagi"

RUN apk add --no-cache python3 \
    && pip3 install --upgrade pip

#ADD . /app

WORKDIR /app

COPY app/index.html ./
COPY app/main.py ./
COPY app/requirements.txt ./

RUN pip3 --no-cache-dir install -r requirements.txt

COPY app /app
EXPOSE 8000

ENTRYPOINT ["python3", "main.py"]