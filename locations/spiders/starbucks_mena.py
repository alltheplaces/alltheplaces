from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class StarbucksMenaSpider(SitemapSpider, StructuredDataSpider):
    name = "starbucks_mena"
    item_attributes = {"brand": "ستاربكس", "brand_wikidata": "Q37158"}
    sitemap_urls = [
        "https://locations.starbucks.ae/robots.txt",
        "https://locations.starbucks.qa/robots.txt",
        "https://locations.starbucks.sa/robots.txt",
        "https://locations.starbucks.eg/robots.txt",
        "https://locations.starbucks.com.bh/robots.txt",
        "https://locations.starbucks.com.kw/robots.txt",
        "https://locations.starbucks.com.lb/robots.txt",
        "https://locations.starbucks.com.om/robots.txt",
    ]
    sitemap_rules = [
        (r"https://locations.starbucks.com.\w+/[a-z-]+/[a-z-]+$", "parse_sd"),
        (r"https://locations.starbucks.\w+/[a-z-]+/[a-z-]+$", "parse_sd"),
        (r"https://locations.starbucks.\w+/fr/[a-z-]+/[a-z-]+$", "parse_sd"),
        (r"https://locations.starbucks.\w+/ar/[a-z-]+/[a-z-]+$", "parse_sd"),
    ]
    wanted_types = ["Restaurant"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["image"] = None
        item["branch"] = item.pop("name").removeprefix("Starbucks ")
        yield item
