# All the Places

[**Website**](https://www.alltheplaces.xyz/)

A project to extract GeoJSON from the web focusing on websites that have 'store locator' pages like restaurants, gas stations, retailers, etc. Each chain has its own bit of software to extract useful information from their site (a "spider"). Each spider can be individually configured to throttle request rate to act as a good citizen on the Internet. The default `User-Agent` for the spiders can be found [here](https://github.com/alltheplaces/alltheplaces/blob/master/locations/settings.py#L20), so websites wishing to prevent our spiders from accessing the data on their website can block that User Agent.

The project is built using [`scrapy`](https://scrapy.org/), a Python-based web scraping framework. Each target website gets its own [spider](https://doc.scrapy.org/en/latest/topics/spiders.html), which does the work of extracting interesting details about locations and outputting results in a useful format.

## Adding a spider

To scrape a new website for locations, you'll want to create a new spider. You can copy from existing spiders or start from a blank, but the result is always a Python class that has a `process()` function that `yield`s [`GeojsonPointItem`s](https://github.com/iandees/all-the-places/blob/master/locations/items.py). The Scrapy framework does the work of outputting the GeoJSON based on these objects that the spider generates.

## Development setup

To get started, you'll want to install the dependencies for this project.

1. This project uses `pipenv` to handle dependencies and virtual environments. To get started, make sure you have [`pipenv` installed](https://github.com/kennethreitz/pipenv#installation).

1. With `pipenv` installed, make sure you have the `all-the-places` repository checked out

   ```
   git clone git@github.com:alltheplaces/alltheplaces.git
   ```

1. Then you can install the dependencies for the project

   ```
   cd alltheplaces
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

   To generate GeoJSON locally, you can enable a couple options during the crawl process to use the GeoJSON exporter and to specify the file to write it to:

   ```
   pipenv run scrapy crawl template \
     --output-format=geojson \
     --output=output.geojson
   ```

1. Finally, make sure your `parse()` function is `yield`ing `GeojsonPointItem`s that contain the location and property data that you extract from the page:

   ```python
   def parse(self, response):
      yield GeojsonPointItem(
          lat=latitude,
          lon=longitude,
          addr_full="1234 Fifth Street",
          city="San Francisco",
          state="CA"
      )
   ```

1. Once you have a spider that logs out useful results, you can create a new branch and push it up to your fork to create a pull request. The build system will run your spider and output information about the results as a comment on your pull request.

## Tips for writing a spider

### Prefer a directory of all locations

Most listings of locations come in two flavors: a "store finder" that lets the user search by location and a "store directory" that is a hierarchical listing of all locations. These listings are sometimes hidden in the footer or on the site map page. Keep an eye out for these, because it's a lot easier if they enumerate all the locations for you rather than having to program a spider to do it for you.  Checking the domain's `robots.txt` file can also be useful for finding sitemaps (http://\<domain>/robots.txt).  

If the only option is search by location, there is likely an AJAX query made to search by latitude/longitude. Keep an eye on your browser's developer tools "network" tab to see what the request is so you can replicate it in your spider.

### Searchable Points

For store locators that do allow search by latitude/longitude, a grid of searchable latlon points representing the centroid of a 100, 50, 25, or 10mile search radius is available for the US and CA [here](https://github.com/alltheplaces/alltheplaces/tree/master/locations/searchable_points). See the [Dollar General scraper](https://github.com/alltheplaces/alltheplaces/pull/1076) for an example of how you might utilize them for national searches.

For stores that do not have a national footprint ([e.g. #1034](https://github.com/alltheplaces/alltheplaces/issues/1034)), there are separate point files that include a state/territory attribute e.g. <i>'us_centroids_100mile_radius_state.csv'</i>. This allows for points to be filtered down to specific states/territories when a national search is unnecessary.

Note: A search radius may overlap multiple states especially when it’s centered near a state boundary. This creates a one to many relationship between the search radius point and the states covered in that search zone. This means that for the state files, there will be records that share the same latlon associated to differing states. The same is true for the CA territory files. 


### You can send the spider to other pages

The simplest thing a spider can do is to load the `start_urls`, process the page, and `yield` the data as `GeojsonPointItem` objects from the `parse()` method. Usually that's not enough to get at useful data, though. The `parse()` method can also `yield` a [Request object](https://doc.scrapy.org/en/latest/topics/request-response.html#request-objects), which scrapy will use to add another URL to the request queue.

By default, the `parse()` method on the spider will be called with the response for the new request. In many cases it's easier to create a new function to parse the new page's content and pass that function in via the `Request` object's `callback` parameter like so:

```python
yield scrapy.Request(
  response.urljoin(store_url.extract()),
  callback=self.parse_store
)
```

Since the next URL you want to request is usually pulled from an `href` in the page and relative to the page you're on, you can use the [`response.urljoin()`](https://doc.scrapy.org/en/latest/topics/request-response.html#scrapy.http.Response.urljoin) method as a shortcut to build the URL for the next request.

### Using the scrapy shell

Instead of running the `scrapy crawl` every time you want to try your spider, you can use the [Scrapy shell](https://doc.scrapy.org/en/latest/topics/shell.html) to load a page and experiment with XPath queries. Once you're happy with the query that extracts interesting data you can use it in your spider. This is a whole lot easier than running the whole crawl command every time you make a change to your spider.

To enter the shell, use `scrapy shell http://example.com` (where you replace the URL with your own). It will dump you into a Python shell after having requested the page and parsing it. Once in the shell, you can do things with the `response` object as if you were in your spider. The shell also offers a shortcut function called `fetch()` that lets you pull up a different page.

## License

The data generated by our spiders is provided [on our website](https://alltheplaces.xyz/) and released under [Creative Commons’ CC-0 waiver](https://creativecommons.org/publicdomain/zero/1.0/).

The [spider software that produces this data](https://github.com/alltheplaces/alltheplaces) (this repository) is licensed under the [MIT license](https://github.com/alltheplaces/alltheplaces/blob/master/LICENSE).
