## Sitemap, for an easy life

The [sitemap](https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview),
and its friend
[robots.txt](https://en.wikipedia.org/wiki/Robots_exclusion_standard), is one of the primary
mechanisms by which sites are able to help search engines, such as Google, extract their
data. The ATP project is analogous to Google but in the vastly more focussed area of POI
generation!

If provided by a site, and mostly they are, then sitemaps act as a machine-readable index
to the site pages. In many cases each POI (store location) has its own web page,
and therefore an individual link in the sitemap. It is also not uncommon for a site to
have a specific index file for its store pages.

If such sitemap data is present then USE IT. Writing bespoke code to query a store
locator web form interface with postcodes or city names is not fun, avoid this if you can.

### SitemapSpider

The sitemap is such an important concept that the [scrapy framework](https://scrapy.org/)
that we use has
[baked in support](https://docs.scrapy.org/en/latest/topics/spiders.html?highlight=sitemapspider#sitemapspider)
for sitemap spider operations, providing a
[few examples](https://docs.scrapy.org/en/latest/topics/spiders.html?highlight=sitemapspider#sitemapspider-examples).

Within our project here are a just few spider examples showing slightly different use of the
`SitemapSpider` support:

* [jackinthebox.py](../locations/spiders/jackinthebox.py)
* [moeys.py](../locations/spiders/moes.py)
* [shopko.py](../locations/spiders/shopko.py)

Note that spiders that have good sitemap links nearly always have
good machine-readable [structured data](./STRUCTURED_DATA.md) for their POI details.
In these cases you will see frequent use of our
[StructuredDataSpider](../locations/structured_data_spider.py)
assist class.

### Developer tooling

We found ourselves inspecting websites so often for sitemap data that we
built a custom scrapy ATP command `scrapy sitemap` to query a site for such
structure. Note the tool is not perfect but in many cases can save digging
around with your web browser in development mode!

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
................. and many more!
```

That is a good start! One of the next steps
could be to analyze one of the store URLs for SEO content
using our [structured data tooling](./STRUCTURED_DATA.md), or give it to a
[schema validation tool](https://validator.schema.org/) which in this case
[yields a good result](https://validator.schema.org/#url=https%3A%2F%2Fsmashburger.com%2Flocations%2Fus%2Fco%2Flafayette%2F2755-dagny-way%2F).
