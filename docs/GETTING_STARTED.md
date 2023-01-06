## Getting started, development setup

The project is Python based (in particular Python 3).
[`scrapy`](https://scrapy.org/), a popular Python-based
web scraping framework, is used to write individual site
[spiders](https://doc.scrapy.org/en/latest/topics/spiders.html).
There are various `scrapy` tutorials,
[this series on YouTube](https://www.youtube.com/watch?v=s4jtkzHhLzY)
is reasonable.

### Development setup

1. Clone a copy of the project from the
   [GitHub All The Places](https://github.com/alltheplaces/alltheplaces/)
   repo (or your own fork if you are considering contributing to the project):

   ```
   $ git clone git@github.com:alltheplaces/alltheplaces.git
   ```

1. If not done so already then
   [install `pipenv`](https://github.com/pypa/pipenv#installation),
   then quickly check it runs:

   ```
   $ pipenv --version
   pipenv, version 2022.8.30
   ```

1. Use `pipenv` to install the project dependencies:

   ```
   $ cd alltheplaces
   $ pipenv install
   ```

1. Test for successful project installation:

   ```
   $ pipenv run scrapy
   ```

   If the above ran without complaint, then you have a
   functional installation and are ready to run and write
   spiders.

### Contributing code

We have a number of guides to help you develop spiders:

* [what should I call my spider?](./SPIDER_NAMING.md)
* [Wikidata and the NSI are an online "brand service"](./WIKIDATA.md)
* [use sitemaps, if available, to find POI pages easily](./SITEMAP.md)
* [data from many POI pages can be extracted without writing code](./STRUCTURED_DATA.md)
* [what is expected in a pull request?](./PULL_REQUEST.md)

### The weekly run

At the time of writing the project performs a [weekly run](./WEEKLY_RUN.md)
of all the spiders, you do not need to do this! In fact, the less the project
"bothers" a website the more we will be tolerated.
