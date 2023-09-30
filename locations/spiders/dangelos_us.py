from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class DangelosUSSpider(SitemapSpider, StructuredDataSpider):
    name = "dangelos_us"
    item_attributes = {"brand": "D'Angelo Grilled Sandwiches", "brand_wikidata": "Q5203069"}
    sitemap_urls = ["https://locations.dangelos.com/robots.txt"]
    sitemap_rules = [(r"com(/\w\w/[-\w]+/[-\w]+)\.html$", "parse")]
