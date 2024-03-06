# All the Places

A project to generate [point of interest (POI)](https://en.wikipedia.org/wiki/Point_of_interest) data sourced [from websites](docs/WHY_SPIDER.md) with 'store location' pages. The project uses [`scrapy`](https://scrapy.org/), a popular Python-based web scraping framework, to execute individual site [spiders](https://doc.scrapy.org/en/latest/topics/spiders.html) that retrieve POI data, publishing the results in a [standard format](DATA_FORMAT.md). There are various `scrapy` tutorials on the Internet and [this series on YouTube](https://www.youtube.com/watch?v=s4jtkzHhLzY) is reasonable.

## Getting started

### Development setup

Windows users may need to follow some extra steps, please follow the [scrapy docs](https://docs.scrapy.org/en/latest/intro/install.html#windows) for up to date details.

#### Ubuntu

These instructions were tested with Ubuntu 22.04.1 LTS on 2024-02-21.

1. Install Python 3 and `pip`:

   ```
   $ sudo apt-get update
   $ sudo apt-get install -y python3 python3-pip python-is-python3
   ```

1. Install `pyenv` and ensure the correct version of Python is available. The following is a summary of the steps, please refer to the [pyenv documentation](https://github.com/pyenv/pyenv#installation) for the most up-to-date instructions.

   ```
   $ sudo apt-get install -y build-essential libssl-dev zlib1g-dev \
         libbz2-dev libreadline-dev libsqlite3-dev curl git \
         libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev \
         libffi-dev liblzma-dev
   $ curl https://pyenv.run | bash
   $ echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.bashrc
   $ echo 'eval "$(pyenv init --path)"' >> ~/.bashrc
   $ echo 'eval "$(pyenv init -)"' >> ~/.bashrc
   $ exec "$SHELL"
   $ pyenv install 3.11
   ```

1. Install `pipenv` and check that it runs:

   ```
   $ pip install --user pipenv
   $ pipenv --version
   pipenv, version 2023.12.1
   ```

1. Clone a copy of the project from the [All the Places](https://github.com/alltheplaces/alltheplaces/) repo (or your own fork if you are considering contributing to the project):

   ```
   $ git clone git@github.com:alltheplaces/alltheplaces.git
   ```

1. Use `pipenv` to install the project dependencies:

   ```
   $ cd alltheplaces
   $ pipenv sync
   ```

1. Test for successful project installation:

   ```
   $ pipenv run scrapy
   ```

   If the above runs without complaint, then you have a functional installation and are ready to run and write spiders.

#### macOS

These instructions were tested with macOS 14.3.1 on 2024-02-21.

1. Install Python 3 and `pip`:

   ```
   $ brew install python@3
   ```

1. Install `pyenv` and ensure the correct version of Python is available. The following is a summary of the steps, please refer to the [pyenv documentation](https://github.com/pyenv/pyenv#installation) for the most up-to-date instructions.

   ```
   $ brew install pyenv
   $ echo 'eval "$(pyenv init --path)"' >> ~/.zshrc
   $ echo 'eval "$(pyenv init -)"' >> ~/.zshrc
   $ exec "$SHELL"
   $ pyenv install 3.11
   ```

1. Install `pipenv` and check that it runs:

   ```
   $ brew install pipenv
   $ pipenv --version
   pipenv, version 2023.12.1
   ```

1. Clone a copy of the project from the [All the Places](https://github.com/alltheplaces/alltheplaces/) repo (or your own fork if you are considering contributing to the project):

   ```
   $ git clone git@github.com:alltheplaces/alltheplaces.git
   ```

1. Use `pipenv` to install the project dependencies:

   ```
   $ cd alltheplaces
   $ pipenv sync
   ```

1. Test for successful project installation:

   ```
   $ pipenv run scrapy
   ```

   If the above runs without complaint, then you have a functional installation and are ready to run and write spiders.

#### Codespaces

You can use GitHub Codespaces to run the project. This is a cloud-based development environment that is created from the project's repository and includes a pre-configured environment with all the tools you need to develop the project. To use Codespaces, click the button below:

   [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/alltheplaces/alltheplaces)

#### Docker

You can use Docker to run the project. This is a container-based development environment that is created from the project's repository and includes a pre-configured environment with all the tools you need to develop the project.

1. Clone a copy of the project from the [All the Places](https://github.com/alltheplaces/alltheplaces/) repo (or your own fork if you are considering contributing to the project):

   ```
   $ git clone git@github.com:alltheplaces/alltheplaces.git
   ```

1. Build the Docker image:

   ```
   $ cd alltheplaces
   $ docker build -t alltheplaces .
   ```

1. Run the Docker container:

   ```
   $ docker run -it alltheplaces
   ```

### Contributing code

Many of the sites provide their data in a [standard format](docs/STRUCTURED_DATA.md). Others export their data [via simple APIs](docs/API_SPIDER.md). We have a number of guides to help you develop spiders:

* [What should I call my spider?](docs/SPIDER_NAMING.md)
* [Using Wikidata and the Name Suggestion Index](docs/WIKIDATA.md)
* [Sitemaps make finding POI pages easier](docs/SITEMAP.md)
* [Data from many POI pages can be extracted without writing code](docs/STRUCTURED_DATA.md)
* [What is expected in a pull request?](docs/PULL_REQUEST.md)
* [What we do behind the scenes](docs/PIPELINES.md)

### The weekly run

The output from running the project is [published on a regular cadence](docs/WEEKLY_RUN.md) to our website: [alltheplaces.xyz](https://www.alltheplaces.xyz/). You should not run all the spiders to pick up the output: the less the project "bothers" a website the more we will be tolerated.

## Contact us

Communication is primarily through tickets on the project GitHub [issue tracker](https://github.com/alltheplaces/alltheplaces/issues). Many contributors are also present on [OSM US Slack](https://slack.openstreetmap.us/), in particular we watch the [#poi](https://osmus.slack.com/archives/CDJ4LKA2Y) channel.

## License

The data generated by our spiders is provided [on our website](https://alltheplaces.xyz/) and released under [Creative Commons’ CC-0 waiver](https://creativecommons.org/publicdomain/zero/1.0/).

The [spider software that produces this data](https://github.com/alltheplaces/alltheplaces) (this repository) is licensed under the [MIT license](https://github.com/alltheplaces/alltheplaces/blob/master/LICENSE).
