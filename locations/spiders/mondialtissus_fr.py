from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class MondialtissusFRSpider(SitemapSpider, StructuredDataSpider):
    name = "mondialtissus_fr"
    item_attributes = {
        "brand": "Mondial Tissus",
        "brand_wikidata": "Q17635288",
    }
    sitemap_urls = ["https://magasins.mondialtissus.fr/robots.txt"]
    sitemap_rules = [
        (r"/tissu-mercerie/[\w-]+/[\w\d]+", "parse"),
    ]
