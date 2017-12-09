FROM python:3

RUN pip install pipenv
WORKDIR /opt/app

COPY Pipfile Pipfile
RUN pipenv install

COPY . .

ENTRYPOINT ["pipenv", "run", "/opt/app/ci/run_all_spiders.sh"]
