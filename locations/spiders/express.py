import json
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser
from locations.structured_data_spider import StructuredDataSpider


class ExpressSpider(SitemapSpider, StructuredDataSpider):
    name = "express"
    item_attributes = {"brand": "Express", "brand_wikidata": "Q1384784"}
    sitemap_urls = [
        "https://stores.express.com/sitemap.xml",
        "https://stores.expressfactoryoutlet.com/sitemap.xml",
    ]
    sitemap_rules = [(r"/[a-z]{2}/[^/]+/[^/]+/[^/]+$", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Any:
        item["image"] = item["name"] = None

        if branch := response.xpath("//title/text()").re_first(r" at (.+?) \|"):
            item["branch"] = branch

        for blob in response.xpath('//script[@type="application/ld+json"]/text()').getall():
            try:
                data = json.loads(blob)
            except json.JSONDecodeError:
                continue
            if subject := data.get("credentialSubject"):
                if geo := subject.get("geo"):
                    item["lat"] = geo.get("latitude")
                    item["lon"] = geo.get("longitude")
                item["opening_hours"] = LinkedDataParser.parse_opening_hours(subject)
                break

        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
