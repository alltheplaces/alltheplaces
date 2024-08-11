## Spidering a Sitemap

The [sitemap](https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview), and its friend [robots.txt](https://en.wikipedia.org/wiki/Robots_exclusion_standard), is one of the primary mechanisms by which sites are able to help search engines index their data. In this case, All the Places is analogous to Google but focuses on POI generation instead of indexing the web.

Sitemaps act as a machine-readable index to the site's pages. In many cases, each store location has its own web page and therefore an individual link in the sitemap. It is also common for a site to have a specific index file for its store pages.

If sitemap data is present then USE IT. Writing code to query a store locator web form interface with postcodes or city names is not fun, avoid this if you can.

### SitemapSpider

The sitemap is such an important concept that the [scrapy framework](https://scrapy.org/) we use has [baked in support](https://docs.scrapy.org/en/latest/topics/spiders.html?highlight=sitemapspider#sitemapspider) for sitemap spider operations, providing a [few examples](https://docs.scrapy.org/en/latest/topics/spiders.html?highlight=sitemapspider#sitemapspider-examples).

Within our project there are a severeal examples showing slightly different use of `SitemapSpider` support:

* [`jackinthebox.py`](../locations/spiders/jack_in_the_box.py)
* [`moeys.py`](../locations/spiders/moes_southwest_grill.py)
* [`shopko.py`](../locations/spiders/shopko.py)

Note that spiders with have good sitemap links nearly always have good machine-readable [structured data](./STRUCTURED_DATA.md) for their POI details. In these cases you will see frequent use of our [`StructuredDataSpider`](../locations/structured_data_spider.py) assistant class.

### Developer tooling

We found ourselves inspecting websites so often for sitemap data that we built a custom scrapy command `scrapy sitemap` to query a site for such structure. Note the tool is not perfect but in many cases can save digging around with your web browser in development mode!

Probe a site for sitemap index files:

```
$ pipenv run scrapy sitemap http://smashburger.com
https://smashburger.com/sitemap_index.xml
https://smashburger.com/post-sitemap.xml
https://smashburger.com/page-sitemap.xml
https://smashburger.com/store-sitemap.xml
https://smashburger.com/give_forms-sitemap.xml
https://smashburger.com/promo-sitemap.xml
https://smashburger.com/item_type-sitemap.xml
```

The store sitemap look interesting, let's see some page links from it:

```
$ pipenv run scrapy sitemap --pages https://smashburger.com/store-sitemap.xml
https://smashburger.com/locations/us/co/glendale/1120-s-colorado-blvd/
https://smashburger.com/locations/us/co/lafayette/2755-dagny-way/
https://smashburger.com/locations/us/co/wheatridge/3356-youngfield-st/
https://smashburger.com/locations/us/co/fort-collins/2550-e-harmony-rd/
https://smashburger.com/locations/us/tx/houston/7811-s-main-street/
https://smashburger.com/locations/us/co/denver/7305-e-35th-avenue/
```

That is a good start! One of the next steps would be to analyze one of the store URLs for SEO content using our [structured data tooling](./STRUCTURED_DATA.md), or give it to a [schema validation tool](https://validator.schema.org/). In the example case, this [yields a good structure data result](https://validator.schema.org/#url=https%3A%2F%2Fsmashburger.com%2Flocations%2Fus%2Fco%2Flafayette%2F2755-dagny-way%2F).
