from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class CuisinellaFRSpider(SitemapSpider, StructuredDataSpider):
    name = "cuisinella_fr"
    item_attributes = {"brand": "Cuisinella", "brand_wikidata": "Q3007012"}
    sitemap_urls = ["https://www.ma.cuisinella/robots.txt"]
    sitemap_rules = [
        (r"/fr-fr/magasins/[\w-]+/[\w-]+", "parse"),
    ]
