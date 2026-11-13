from typing import Iterable

from scrapy import Spider
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser


class AriatSpider(Spider):
    name = "ariat"
    item_attributes = {"brand": "Ariat", "brand_wikidata": "Q4790264"}
    # Ariat's own stores only; the Locally storefinder also lists thousands of dealers.
    start_urls = ["https://stores.ariat.com/brand"]

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        for ld in LinkedDataParser.iter_linked_data(response):
            if not LinkedDataParser.check_type(ld.get("@type"), "LocalBusiness"):
                continue
            item = LinkedDataParser.parse_ld(ld)
            item["ref"] = ld.get("url")
            item["branch"] = item.pop("name", None)
            item.pop("image", None)
            apply_category(Categories.SHOP_CLOTHES, item)
            yield item
