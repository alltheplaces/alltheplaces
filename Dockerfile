FROM python:3

RUN pip install pipenv
WORKDIR /opt/app

# Used by the run all spiders script to build output JSON
RUN apt-get update \
    && apt-get install -y jq zip \
    && rm -rf /var/lib/apt/lists/*

COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock
RUN pipenv install --dev --deploy --system

RUN pipenv run playwright install firefox
RUN playwright install-deps

COPY . .

CMD ["/opt/app/ci/run_all_spiders.sh"]
