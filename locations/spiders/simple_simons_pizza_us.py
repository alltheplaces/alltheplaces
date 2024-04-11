import re

from locations.items import Feature
from locations.storefinders.storepoint import StorepointSpider


class SimpleSimonsPizzaUSSpider(StorepointSpider):
    name = "simple_simons_pizza_us"
    item_attributes = {"brand": "Simple Simon's Pizza", "brand_wikidata": "Q116737866"}
    key = "15dbb16b507995"

    def parse_item(self, item: Feature, location: dict, **kwargs):
        if " - COMING SOON" in item["name"]:
            return  # TODO?
        if m := re.match(r"(.+) \(inside (.+)\)\s?$", item["name"]):
            item["branch"], item["located_in"] = m.groups()
            item["name"] = None
        else:
            item["branch"] = item.pop("name")

        yield item
