FROM python:3.6

RUN pip install pipenv
WORKDIR /opt/app

# Used by the run all spiders script to build output JSON
RUN apt-get update \
    && apt-get install -y jq \
    && rm -rf /var/lib/apt/lists/*

COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock
RUN pipenv install --dev --deploy --system

COPY . .

CMD ["/opt/app/ci/run_all_spiders.sh"]
