import re

from locations.hours import OpeningHours
from locations.storefinders.store_locator_plus_self import StoreLocatorPlusSelfSpider

branch_separator = re.compile(r"^\s*-\s*Lee&#039;s Sandwiches\s+")


class LeesSandwichesUSSpider(StoreLocatorPlusSelfSpider):
    name = "lees_sandwiches_us"
    item_attributes = {
        "brand_wikidata": "Q6512823",
        "brand": "Lee's Sandwiches",
    }
    allowed_domains = ["leesandwiches.com"]
    iseadgg_countries_list = ["US"]
    search_radius = 158
    max_results = 50
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse_item(self, item, location, **kwargs):
        if "Coming Soon" in item["name"]:
            return
        item["extras"]["fax"] = location["fax"]
        item["image"] = location["image"]
        item["branch"] = branch_separator.sub("", item.pop("name").removeprefix(location["city"]))

        oh = OpeningHours()
        oh.add_ranges_from_string(location["hours"])
        item["opening_hours"] = oh

        yield item
