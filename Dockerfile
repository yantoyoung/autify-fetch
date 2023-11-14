FROM python:3.12-bookworm
MAINTAINER Yanto Young <yanto.young@rwth-aachen.de>

ENV PYTHONUNBUFFERED 1

RUN mkdir -p /app
ADD ./requirements.txt /app/
RUN pip install -r /app/requirements.txt

WORKDIR /app
