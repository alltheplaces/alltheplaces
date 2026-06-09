import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.locally import LocallySpider


class FjallravenSpider(LocallySpider):
    name = "fjallraven"
    item_attributes = {"brand": "Fjällräven", "brand_wikidata": "Q1422481"}
    company_id = 1392
    categories = ["brandstore", "Outlet"]

    def post_process_item(self, item: Feature, response: TextResponse, location: dict) -> Iterable[Feature]:
        if store_name := item.pop("name", None):
            item["branch"] = re.sub(r"^Fj[äa]llr[äa]ven\s*-?\s*", "", store_name)
        item["street_address"] = item.pop("addr_full")
        apply_category(Categories.SHOP_OUTDOOR, item)
        yield item
