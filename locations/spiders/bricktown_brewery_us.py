from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.storerocket import StoreRocketSpider


class BricktownBreweryUSSpider(StoreRocketSpider):
    name = "bricktown_brewery_us"
    item_attributes = {"brand": "Bricktown Brewery"}
    storerocket_id = "wzpAvNm4dD"
    time_hours_format = 12

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["ref"] = str(item["ref"])
        item["branch"] = (item.pop("name", None) or "").strip()
        # The address components are all present, so the joined string is not
        # needed alongside them.
        item.pop("addr_full", None)
        # The API leaves country blank on most records; every restaurant is in
        # the US.

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "american"
        item["extras"]["microbrewery"] = "yes"

        yield item
