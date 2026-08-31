from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class Apotek1NOSpider(JSONBlobSpider):
    name = "apotek_1_no"
    item_attributes = {"brand": "Apotek 1", "brand_wikidata": "Q4581428"}
    start_urls = [
        "https://api.apotek1.no/wcs/resources/store/10151/storelocator/latitude/0/longitude/0?maxItems=1000&radius=2500000&siteLevelStoreSearch=false"
    ]
    locations_key = "PhysicalStore"

    def pre_process_data(self, feature: dict) -> None:
        # Strip padded string values
        for k, v in feature.items():
            if isinstance(v, str):
                feature[k] = v.strip()
        # Flatten Attribute array into the feature dict for easier access
        for attr in feature.pop("Attribute", []):
            feature[attr["name"]] = attr["value"]

    def post_process_item(self, item: Feature, response: TextResponse, store: dict) -> Iterable[Feature]:
        # Filter out third party stores used for pickup (commissioners)
        if store["storeName"].startswith("Comm-"):
            return

        item["ref"] = store["storeName"]
        # DictParser sets `name` from the numeric storeName; clear it so name is derived from brand + branch
        item["name"] = None
        item["extras"]["fax"] = store["fax1"]
        item["state"] = store["stateOrProvinceName"]

        state_slug = store["stateOrProvinceName"].lower().replace(" ", "-")
        item["website"] = (
            f"https://www.apotek1.no/vaare-apotek/{state_slug}/{store['RelativeURL']}-{store['storeName']}"
        )

        if descriptions := store.get("Description"):
            item["branch"] = descriptions[0]["displayStoreName"].removeprefix("Apotek 1 ").strip()

        if disable_pickup := store.get("disablePickup"):
            apply_yes_no(Extras.TAKEAWAY, item, disable_pickup == "false", False)

        oh = OpeningHours()
        for day in DAYS_FULL:
            if (start := store[f"Open{day}"]) != "STENGT":
                oh.add_range(day, start, store[f"Close{day}"])
        item["opening_hours"] = oh

        apply_category(Categories.PHARMACY, item)

        yield item
