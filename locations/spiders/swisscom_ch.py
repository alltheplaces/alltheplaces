import json
from typing import Any, Iterable

from scrapy.http import Response, TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser
from locations.structured_data_spider import StructuredDataSpider


class SwisscomCHSpider(SitemapSpider, StructuredDataSpider):
    name = "swisscom_ch"
    item_attributes = {"brand": "Swisscom", "brand_wikidata": "Q644324"}
    sitemap_urls = ["https://swisscomshops.swisscom.ch/en/sitemap.xml"]
    sitemap_rules = [(r"/en/[^/]+/[^/]+$", "parse")]
    wanted_types = ["LocalBusiness"]

    def iter_linked_data(self, response: Response) -> Iterable[dict]:
        for ld_obj in LinkedDataParser.iter_linked_data(response, self.json_parser):
            if ld_obj.get("@type") == "ItemList":
                yield from ld_obj["itemListElement"]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if item["name"].startswith("Swisscom Shop"):
            item["branch"] = item.pop("name").removeprefix("Swisscom Shop").strip(" -")
        apply_category(Categories.SHOP_TELECOMMUNICATION, item)
        yield item
