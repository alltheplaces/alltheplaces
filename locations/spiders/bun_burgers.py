from html import unescape
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class BunBurgersSpider(AgileStoreLocatorSpider):
    name = "bun_burgers"
    item_attributes = {"brand": "Bun Burgers", "brand_wikidata": "Q140876293"}
    allowed_domains = ["bunburgers.com"]
    skip_auto_cc_domain = True

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if addr := item.get("street_address"):
            item["street_address"] = unescape(addr)
        item["branch"] = (
            item.pop("name", "")
            .strip()
            .removeprefix("Bun Burgers - ")
            .removeprefix("Bun Burgers ")
            .strip()
            or None
        )
        item["website"] = "https://bunburgers.com/dove-siamo/"
        item.pop("state", None)
        apply_category(Categories.FAST_FOOD, item)
        apply_category({"cuisine": "burger"}, item)
        yield item
