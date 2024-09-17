from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class BoelsSpider(SitemapSpider, StructuredDataSpider):
    name = "boels"
    item_attributes = {
        "brand": "Boels Rental",
        "brand_wikidata": "Q19901961",
    }
    sitemap_urls = ["https://www.boels.com/robots.txt"]
    sitemap_rules = [
        (r"https://www.boels.com/en-\w\w/branches/[\w+]", "parse"),
    ]
