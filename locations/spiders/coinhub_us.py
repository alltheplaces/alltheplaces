from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.storepoint import StorepointSpider


class CoinhubUSSpider(StorepointSpider):
    name = "coinhub_us"
    item_attributes = {"brand": "Coinhub", "brand_wikidata": "Q126195855"}
    key = "162cb508a25fa2"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["ref"] = str(item["ref"])
        if " inside: " in item["name"]:
            item["located_in"] = item["name"].split(" inside: ", 1)[1]
        item.pop("name", None)
        item.pop("phone", None)
        item.pop("email", None)
        apply_category(Categories.ATM, item)
        item["extras"]["currency:XBT"] = "yes"
        item["extras"]["currency:USD"] = "yes"
        item["extras"]["cash_in"] = "yes"
        item["extras"]["cash_out"] = "no"
        yield item
