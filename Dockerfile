FROM python:3

RUN pip install pipenv
WORKDIR /opt/app
COPY . .
RUN pipenv install
