from typing import Any, AsyncIterator, Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.items import Feature, get_merged_item
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingEGSpider(JSONBlobSpider):
    name = "burger_king_eg"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    locations_key = "data"
    stored_items = {}

    async def start(self) -> AsyncIterator[Any]:
        yield JsonRequest(
            url="https://api.solo.skylinedynamics.com/locations?_lat=0&_long=0",
            headers={
                "solo-concept": "cQhyxA8MVeI",
                "accept-language": "en-us",
            },
            meta={"language": "en"},
            dont_filter=True,
        )
        yield JsonRequest(
            url="https://api.solo.skylinedynamics.com/locations?_lat=0&_long=0",
            headers={
                "solo-concept": "cQhyxA8MVeI",
                "accept-language": "ar-sa",
            },
            meta={"language": "ar"},
            dont_filter=True,
        )

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        item["branch"] = location["attributes"]["name"].removeprefix("Burger King").replace("برجر كينج", "").strip(" -")
        item["lat"] = location["attributes"]["lat"]
        item["lon"] = location["attributes"]["long"]
        item["phone"] = location["attributes"]["telephone"]
        item["email"] = location["attributes"]["email"]
        item["addr_full"] = location["attributes"]["line1"]
        # item["country"] = location["attributes"]["country"] # Incorrect country (SA) reported for some locations

        apply_category(Categories.FAST_FOOD, item)
        apply_yes_no(Extras.DELIVERY, item, location["attributes"]["delivery-enabled"] == 1, False)
        apply_yes_no(Extras.DRIVE_THROUGH, item, location["attributes"]["is-drive-thru-enabled"], False)

        try:
            item["opening_hours"] = self.parse_opening_hours(location)
        except:
            self.logger.error("Failed to parse opening hours {}".format(location["attributes"].get("opening-hours")))

        if item["ref"] in self.stored_items:
            other_item = self.stored_items.pop(item["ref"])
            if response.meta["language"] == "en":
                yield get_merged_item({"en": item, "ar": other_item}, "ar")
            else:
                yield get_merged_item({"en": other_item, "ar": item}, "ar")
        else:
            self.stored_items[item["ref"]] = item

    def parse_opening_hours(self, location: dict) -> OpeningHours:
        oh = OpeningHours()
        if location["attributes"]["open-24-hours"]:
            oh = "Mo-Su 00:00-24:00"
        elif location["attributes"]["opening-hours"] is not None:
            for rule in location["attributes"]["opening-hours"]:
                oh.add_range(DAYS[int(rule["day"])], rule["open"], rule["closed"])
        return oh
