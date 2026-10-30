from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.storerocket import StoreRocketSpider


class PrecisionTuneAutoCareUSSpider(StoreRocketSpider):
    name = "precision_tune_auto_care_us"
    item_attributes = {"brand": "Precision Tune Auto Care"}
    storerocket_id = "xw8VVEg8aE"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["ref"] = str(item["ref"])
        item["branch"] = (item.pop("name", None) or "").strip()
        # The address components are all present, so the joined string is not
        # needed alongside them.
        item.pop("addr_full", None)
        # Two centres on military bases leave country blank.

        apply_category(Categories.SHOP_CAR_REPAIR, item)

        yield item
