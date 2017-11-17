# All the Places

A project to extract GeoJSON from the web focusing on websites that have 'store locator' pages like restaurants, gas stations, retailers, etc.

The project is built using [`scrapy`](https://scrapy.org/), a Python-based web scraping framework. Each target website gets its own [spider](https://doc.scrapy.org/en/latest/topics/spiders.html), which does the work of extracting interesting details about locations and outputting results in a useful format.

## Adding a spider

To scrape a new website for locations, you'll want to create a new spider. You can copy from existing spiders or start from a blank, but the result is always a Python class that has a `process()` function that `yield`s [`GeojsonPointItem`s](https://github.com/iandees/all-the-places/blob/master/locations/items.py). The Scrapy framework does the work of outputting the GeoJSON based on these objects that the spider generates.

## Development setup

To get started, you'll want to install the dependencies for this project.

1. This project uses `pipenv` to handle dependencies and virtual environments. To get started, make sure you have [`pipenv` installed](https://github.com/kennethreitz/pipenv#installation).

1. With `pipenv` installed, make sure you have the `all-the-places` repository checked out

   ```
   git clone git@github.com:iandees/all-the-places.git
   ```

1. Then you can install the dependencies for the project

   ```
   cd all-the-places
   pipenv install
   ```

1. After dependencies are installed, make sure you can run the `scrapy` command without error

   ```
   pipenv run scrapy
   ```

1. If `pipenv run scrapy` ran without complaining, then you have a functional `scrapy` setup and are ready to write a scraper.

## Create a new spider

1. Create a new file in `locations/spiders/` with this content:

    ```python
    # -*- coding: utf-8 -*-
    import scrapy
    from locations.items import GeojsonPointItem

    class TemplateSpider(scrapy.Spider):
        name = "template"
        allowed_domains = ["www.sample.com"]
        start_urls = (
            'https://www.sample.com/locations/',
        )

        def parse(self, response):
            pass
    ```

    This blank/template spider will start at the given `start_urls`, only touch the domains listed in `allowed_domains`, and all web requests will be returned to the `parse()` function with response content in the `response` argument. Once you have the response content, you can perform various operations on it. For example, the most useful is probably running [XPath](https://developer.mozilla.org/en-US/docs/Web/XPath) selections on the HTML of the page to extract data out of the page. Check out the "Scraper tips" section below for more information about how to use these tools to efficiently get data out of the page.

1. Once you have your spider written, you can give it a test run to make sure it's finding the expected results.

   ```
   pipenv run scrapy crawl template
   ```

   The `scrapy crawl template` command runs a spider named `template`. If you changed the name of your spider, you should use the name you chose. By default, `scrapy crawl` does not save the output anywhere, but it does log the results of the spider operation fairly verbosely.

1. Finally, make sure your `parse()` function is `yield`ing `GeojsonPointItem`s that contain the location and property data that you extract from the page:

   ```python
   def parse(self, response):
      yield GeojsonPointItem(
          properties=properties,
          lon_lat=lon_lat,
      )
   ```

1. Once you have a spider that logs out useful results, you can create a new branch and push it up to your fork to create a pull request. The build system will run your spider and output information about the results as a comment on your pull request.

## Scraper tips

### You can spider to other pages

### Using the scrapy shell
