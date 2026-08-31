from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.sylinder import SylinderSpider


class WoltMarketNOSpider(SylinderSpider):
    name = "wolt_market_no"
    item_attributes = {"name": "Wolt Market", "brand": "Wolt Market", "brand_wikidata": "Q30024526"}
    # Wolt Market stores are no longer assigned a chain id, so the
    # full store list is requested and matched on store slug instead.
    app_keys = []
    warn_if_no_base_url = False

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        for location in response.json():
            if location["storeDetails"]["slug"].startswith("wolt-market-"):
                yield from self.parse_location(location)

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Wolt Market ").removesuffix(" DV")
        apply_category(Categories.DARK_STORE_GROCERY.value, item)
        yield item
