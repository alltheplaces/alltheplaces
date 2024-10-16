import re
from html import unescape

from geonamescache import GeonamesCache
from scrapy import Selector

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.super_store_finder import SuperStoreFinderSpider


class TacoPalenqueSpider(SuperStoreFinderSpider):
    name = "taco_palenque"
    item_attributes = {
        "brand_wikidata": "Q7673965",
        "brand": "Taco Palenque",
    }
    allowed_domains = [
        "www.tacopalenque.com",
    ]

    def get_us_state_code_from_address(self, address: str) -> bool:
        states = GeonamesCache.us_states
        # state is either at the end or right before the ZIP
        split_address = re.split(r"[\s,]+", address.upper())[-2:]
        for key in states:
            state_code = states[key]["code"]
            state_name = states[key]["name"]
            if state_code in split_address or state_name.upper() in split_address:
                return state_code
        return None

    def parse_item(self, item: Feature, location: Selector):
        item["branch"] = unescape(item.pop("name"))

        # this makes the assumption that the chain only exists in US and Mexico
        state_code = self.get_us_state_code_from_address(item["addr_full"])
        if state_code is not None:
            item["state"] = state_code
            item["country"] = "US"
        else:
            item["country"] = "MX"

        apply_category(Categories.FAST_FOOD, item)

        yield item
