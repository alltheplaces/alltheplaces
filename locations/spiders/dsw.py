import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import apply_category, Categories
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class DswSpider(SitemapSpider, StructuredDataSpider):
    name = "dsw"
    item_attributes = {"brand": "DSW", "brand_wikidata": "Q5206207"}
    allowed_domains = [
        "stores.dsw.com",
        "stores.dsw.ca",
    ]
    sitemap_urls = [
        "https://stores.dsw.com/sitemap.xml",
        "https://stores.dsw.ca/sitemap.xml",
    ]
    sitemap_rules = [
        (r"ca/\w\w/[^/]+\/[^/]+$","parse_sd"),
        (r"usa/\w\w/[^/]+/[^/]+\.html$", "parse_sd"),
    ]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Any:
        item["name"] = item["image"] = None

        if map_src := response.xpath(
            '//source[contains(@srcset, "https://api.mapbox.com/styles/v1/mapbox/streets-v12/static/pin")]/@srcset'
        ).get():
            if m := re.search(r"\((-?\d+\.\d+),(-?\d+\.\d+)\)", map_src):
                item["lon"], item["lat"] = m.groups()
        apply_category(Categories.SHOP_SHOES, item)

        yield item
