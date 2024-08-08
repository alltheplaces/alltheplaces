## Structured data, POIs that are not shy!

The web is full of information. A lot you can see, it is rendered by your browser. Some you cannot see, it is intended for consumption by machines, part of the so-called semantic web. Many POI web pages have embedded data which describe attributes of the POI such as address, latitude/longitude, opening hours and more. Google have an excellent tutorial on [how structured data works](https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data).

More information can be found at [schema.org](https://schema.org/). Various online resources are available such as the [schema validation tool](https://validator.schema.org/) to help you extract structured data on an ad-hoc basis from a URL. For example, the web page for this [smashburger location](https://smashburger.com/locations/us/co/lafayette/2755-dagny-way/) decodes to [yield this structured data](https://validator.schema.org/#url=https%3A%2F%2Fsmashburger.com%2Flocations%2Fus%2Fco%2Flafayette%2F2755-dagny-way%2F).

### StructuredDataSpider

The ATP project has custom library code which helps with the creation of spiders for sites which provide structured data in their pages. One key class provided is [StructuredDataSpider](../locations/structured_data_spider.py).

An ATP spider will typically use [CrawlSpider](https://docs.scrapy.org/en/latest/topics/spiders.html#crawlspider) or, more commonly, [SitemapSpider](https://docs.scrapy.org/en/latest/topics/spiders.html#sitemapspider) to drive the `scrapy` engine to call the `parse_sd` method in [StructuredDataSpider](../locations/structured_data_spider.py) for an individual POI page.

The `parse_sd` method will look for default `wanted_types` in the page. The spider can override this value if it is not appropriate. If required the spider can clean up source data with `pre_process_data` and clean up the item, or add extra attributes with `post_process_item`.

This is best illustrated by reference to some example spiders in the project:

* [jackinthebox.py](../locations/spiders/jack_in_the_box.py) (as simple as it gets!)
* [petco.py](../locations/spiders/petco.py) (totally declarative, sitemap filter for store pages)
* [wickes_gb.py](../locations/spiders/wickes_gb.py) (post-process example)
* [subway.py](../locations/spiders/subway.py) (pre-process example)
* [webuyanycar_gb.py](../locations/spiders/webuyanycar_gb.py) (a CrawlSpider example)

### `scrapy sd` can help

Following on from the `smashburger` example in our [sitemap tool](./SITEMAP.md) example then we can run the `scrapy sd` custom tool on one of the URLs:

```
$ pipenv run scrapy sd https://smashburger.com/locations/us/co/lafayette/2755-dagny-way/
{'city': 'Lafayette',
 'image': 'https://smashburger.com/wp-content/uploads/2021/03/SB_hori_logo_Lt_NoTag_TM_RGB_XL.png',
 'lat': '40.0131850',
 'lon': '-105.1315620',
 'name': 'Your Neighborhood Smashburger',
 'opening_hours': 'Mo-Th 10:30-21:30; Fr-Sa 10:30-22:00; Su 10:30-21:30',
 'phone': '13039269700',
 'postcode': '80026',
 'ref': '1001',
 'state': 'CO',
 'street_address': '2755 Dagny Way,',
 'website': 'https://smashburger.com/locations/us/co/lafayette/2755-dagny-way/'}
```

This is good as it shows that `smashburger` can be very easily processed, as we do in [smashburger.py](../locations/spiders/smashburger.py).

Note that the spider we wrote has [Wikidata](./WIKIDATA.md) included. To get an idea of the kind of output this enables re-run the `scrapy sd` tool but this time pass a Wikidata QID for it to use:

```
pipenv run scrapy sd -O smashburger.geojson --wikidata Q17061332 https://smashburger.com/locations/us/co/lafayette/2755-dagny-way/
```

The single POI has been written as output to the `smashburger.geojson` file shown below:

```json
{"type":"FeatureCollection","features":[{"type": "Feature", "id": "d9bWFhLsLRtombN0CN2nyIJozyY=", "properties": {"ref": "1001", "@spider": "my_spider", "nsi_id": "smashburger-d2abf0", "amenity": "fast_food", "cuisine": "burger", "takeaway": "yes", "addr:street_address": "2755 Dagny Way,", "addr:city": "Lafayette", "addr:state": "CO", "addr:postcode": "80026", "name": "Your Neighborhood Smashburger","phone": "13039269700", "website": "https://smashburger.com/locations/us/co/lafayette/2755-dagny-way/", "opening_hours": "Mo-Th 10:30-21:30; Fr-Sa 10:30-22:00; Su 10:30-21:30", "image": "https://smashburger.com/wp-content/uploads/2021/03/SB_hori_logo_Lt_NoTag_TM_RGB_XL.png", "brand": "Smashburger", "brand:wikidata": "Q17061332"}, "geometry": {"type": "Point", "coordinates": [-105.131562, 40.013185]}}]}
```

Note that the [ATP pipeline](../locations/pipelines/apply_nsi_categories.py) code has used the QID to apply OSM POI category tags, from NSI, to the output: `"amenity": "fast_food", "cuisine": "burger", "takeaway": "yes"`.

The `smashburger.geojson` file can be examined in any number of tools, a popular choice here is [geojson.io](https://geojson.io/).

The ATP tooling described here and on related pages can go a long way to giving you confidence in your end spider before writing any code!
