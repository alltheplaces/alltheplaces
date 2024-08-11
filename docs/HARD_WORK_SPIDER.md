## Hard work spider

Many sites export clean [structured data](./STRUCTURED_DATA.md) or have a simple [JSON API](./API_SPIDER.md) available. Many sites index their store pages with a [sitemap](./SITEMAP.md). A good deal of other sites are what we might call **hard work**, lacking much of the aforementioned support. These sites are to be avoided, if you can, [but if you must](./WHY_SPIDER.md), then we have some tips to help with writing your spider.

### Common patterns

#### Site embeds JSON or Javascript hash ("JS Blob")

```
<script>var markers = [{....}, {....}]</script>
```

Use xpath and `parse_js_object` to extract the content; suitable for `DictParser`.

Example: [a1_rs](../locations/spiders/a1_rs.py)
```
    def parse(self, response):
        cities_js = (
            response.xpath('//script[contains(text(), "var cities_json = ")]/text()')
            .get()
            .split("var cities_json = ", 1)[1]
            .split("}];", 1)[0]
            + "}]"
        )
        cities_dict = parse_js_object(cities_js)
```

#### Coordinates as google urls

Use `locations.google_url.extract_google_position` - see [averitt](../locations/spiders/averitt.py)

#### Site uses a HTML list of links to other store pages

Use `CrawlSpider` and LinkExtractor rules - see [crew_clothing_gb](../locations/spiders/crew_clothing_gb.py)

```
rules = [Rule(LinkExtractor(r"/customer-services/stores/[-\w]+/$"), "parse_sd")]
```

### Using the scrapy shell

Digging around in HTML responses for data is fiddly.

Instead of `pipenv run scrapy crawl` every time you want to try your spider, you can use the [`scrapy shell`](https://doc.scrapy.org/en/latest/topics/shell.html) to load a page and experiment with XPath queries. When you're happy with the query, you can use it in your code. This is a lot easier than running a `crawl` every time you make a change to your spider.

To enter the shell, use `pipenv run scrapy shell http://example.com` (where you replace the URL with your own). It will dump you into a Python shell after having requested the page and parsing it. Once in the shell, you can do things with the `response` object as if you were in your spider. The shell also offers a shortcut function called `fetch()` that lets you pull up a different page, once again setting the `response` object.

For example from within the `scrapy shell`:

```
>>> fetch("https://www.wickes.co.uk/store/8093")
2022-11-06 14:02:14 [scrapy.core.engine] DEBUG: (200) <GET https://www.wickes.co.uk/store/8093>
>>> response.xpath("//@data-latitude").get()
'51.446565'
>>> fetch("https://www.wickes.co.uk/store/8093")
2022-11-06 14:02:18 [scrapy.core.engine] DEBUG: (200) <GET https://www.wickes.co.uk/store/8093>
```

Use your **&#8593;** (up-arrow) key to recall and edit previous command lines in the shell session, you will use this quite regularly to refine your XPath query until happy.

### Keep your XPath queries simple

Or as simple as you **sensibly** can. For example, using a query which is extremely brittle to the structure of the HTML is a very bad idea. For example:

```python
item["lat"] = response.xpath("/html/body/section/div[2]/div[{}]/div[1]//@data-latitude").get()
```

is not a good idea, when if as is most likely, there is only one such attribute on the page, this works:

```python
item["lat"] = response.xpath("//@data-latitude").get()
```

Some people will write lots of code to extract every last piece of POI data from a page. Do not fall for this temptation, do what is important and easy.

### Our libraries may still be of help

Remember that many of our libraries may prove helpful to you, even though they are primarily intended for more structured data.

You may be able to form a useful dictionary without too much effort then give it to [DictParser](../locations/dict_parser.py).

[OpeningHours](../locations/hours.py) will also be useful if your site is important enough to merit the effort.

### Hybrid spider

Frequently you will find that a site exports most of its information simply (for example via structured data), but that some important fields may only be retrieved by digging around in the HTML.

For example, the [wikckes_gb.py](../locations/spiders/wickes_gb.py) spider is a very simple example of good structured data present but not latitude and longitude. These are available but must be dug out of the page with a `response.xpath` query.

### Coordinate Reference Systems

All our spiders emit geographic coordinates as latitude/longitude pairs according to the World Geodetic System WGS84, which is used by GPS and nearly all online mapping services. To convert coordinates from other reference systems to WGS84, we use [proj](https://proj.org/) via its Python wrapper [pyproj](https://pyproj4.github.io/pyproj/stable/examples.html).  For example, the [winterthur_ch.py](../locations/spiders/winterthur_ch.py) spider converts [Swiss CH1903+/LV95 coordinates](https://epsg.io/2056) to WGS84.

### Doing is learning

The bottom line here is that a lot of the techniques for spidering POI data you will learn by experience. The inquisitive may also look around existing spiders for possible inspiration. There is always some new "trick" to learn!
