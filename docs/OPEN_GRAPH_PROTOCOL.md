## Open Graph Protocol

Similar to [Structured Data](./docs/STRUCTURED_DATA.md]; [Open Graph Protocol](https://ogp.me) is a way for sites to assert facts in the `<meta>` tags of their websites.

While this can be any RDFa/Schema.org/similar terminology, it is commonly used with open graph specific vocabularies.

Example:
```
<meta name="geo.position" content="51.515637209437, -0.17522994453623" />
<meta name="geo.placename" content="Budgens Praed Street" />
<meta name="icbm" content="51.515637209437, -0.17522994453623" />
<meta name="geo.region" content="GB" />
<link rel="canonical" href="https://www.budgens.co.uk/our-stores/praed-street" />
<meta property="og:site_name" content="Budgens.co.uk" />
<meta property="og:type" content="store" />
<meta property="og:url" content="https://www.budgens.co.uk/our-stores/praed-street" />
<meta property="og:title" content="Budgens Praed Street" />
<meta property="place:location:latitude" content="51.515637209437" />
<meta property="place:location:longitude" content="-0.17522994453623" />
<meta property="og:street_address" content="171-173 Praed Street," />
<meta property="og:locality" content="Paddington" />
<meta property="og:region" content="London" />
<meta property="og:postal_code" content="W2 1RH" />
<meta property="og:country_name" content="United Kingdom" />
<meta property="og:phone_number" content="0207 402 3117" />
```


### OpenGraphSpider

The ATP project has custom library code which helps with the creation of spiders for sites which provide open graph data in their pages. One key class provided is [OpenGraphSpider](../locations/open_graph_spider.py).

An ATP spider will typically use [CrawlSpider](https://docs.scrapy.org/en/latest/topics/spiders.html#crawlspider) or, more commonly, [SitemapSpider](https://docs.scrapy.org/en/latest/topics/spiders.html#sitemapspider) to drive the `scrapy` engine to call the `parse_og` method in [OpenGraphSpider](../locations/open_graph_spider.py) for an individual POI page.

This is best illustrated by reference to some example spiders in the project:

* [londis_gb.py](../locations/spiders/londis_gb.py) (as simple as it gets!)
* [premier_gb.py](../locations/spiders/premier_gb.py) (post processing)

### `scrapy og` can help

We can run the `scrapy og` custom tool on one of the URLs:

```
$ pipenv run scrapy og https://www.budgens.co.uk/our-stores/praed-street
{'city': 'Paddington',
 'country': 'United Kingdom',
 'email': None,
 'extras': {},
 'housenumber': None,
 'lat': '51.515637209437',
 'lon': '-0.17522994453623',
 'name': 'Budgens Praed Street',
 'phone': '0207 402 3117',
 'postcode': 'W2 1RH',
 'ref': 'https://www.budgens.co.uk/our-stores/praed-street',
 'state': 'London',
 'street': None,
 'street_address': '171-173 Praed Street,',
 'website': 'https://www.budgens.co.uk/our-stores/praed-street'}
```
