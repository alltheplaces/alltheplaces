FROM python:3

RUN pip install pipenv
WORKDIR /opt/app

COPY Pipfile Pipfile
RUN pipenv install --dev

COPY . .

ENTRYPOINT ["pipenv", "run", "python", "/opt/app/ci/run_all_spiders.py"]
