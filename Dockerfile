FROM python:3.8

ENV PYTHONUNBUFFERED 1

RUN mkdir -p /app
RUN mkdir -p /root/.aws

COPY ./requirements.txt /app/requirements.txt

RUN pip install --upgrade pip
RUN pip install -r /app/requirements.txt

COPY . /app/
COPY ./aws /root/.aws

WORKDIR /app/

EXPOSE 8000
