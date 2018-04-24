FROM python:3

RUN pip install pipenv
WORKDIR /opt/app

COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock
RUN pipenv install --dev --deploy --system

COPY . .

CMD ["/opt/app/ci/run_all_spiders.sh"]
