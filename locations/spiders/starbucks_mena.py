import json

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class StarbucksMenaSpider(SitemapSpider, StructuredDataSpider):
    name = "starbucks_mena"
    item_attributes = {"brand": "ستاربكس", "brand_wikidata": "Q37158"}
    sitemap_urls = [
        "https://locations.starbucks.ae/robots.txt",
        "https://locations.starbucks.qa/sitemap.xml",
        "https://locations.starbucks.sa/sitemap.xml",
        "https://locations.starbucks.eg/sitemap.xml",
        "https://locations.starbucks.com.bh/sitemap.xml",
        "https://locations.starbucks.com.kw/sitemap.xml",
        "https://locations.starbucks.com.lb/sitemap.xml",
        "https://locations.starbucks.com.om/sitemap.xml",
    ]
    sitemap_rules = [
        (r"https://locations.starbucks.com.\w+/[a-z-]+/[a-z-]+$", "parse_sd"),
        (r"https://locations.starbucks.\w+/[a-z-]+/[a-z-]+$", "parse_sd"),
        (r"https://locations.starbucks.\w+/fr/[a-z-]+/[a-z-]+$", "parse_sd"),
        (r"https://locations.starbucks.\w+/ar/[a-z-]+/[a-z-]+$", "parse_sd"),
    ]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["image"] = None
        item["branch"] = item.pop("name").removeprefix("Starbucks ")
        ld_data = (
            json.loads(response.xpath('//*[@type="application/ld+json"][2]//text()').get())
            .get("credentialSubject")
            .get("geo")
        )
        item["lat"] = ld_data.get("latitude")
        item["lon"] = ld_data.get("longitude")
        yield item
