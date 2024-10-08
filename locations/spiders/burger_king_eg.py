from scrapy.http import JsonRequest

from locations.categories import Extras, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.items import get_merged_item
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingEGSpider(JSONBlobSpider):
    name = "burger_king_eg"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = ["https://api.solo.skylinedynamics.com/locations?_lat=0&_long=0"]
    locations_key = "data"
    stored_items = {}

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(
                url=url,
                headers={
                    "solo-concept": "cQhyxA8MVeI",
                    "accept-language": "en-us",
                },
                meta={"language": "en"},
                dont_filter=True,
            )
            yield JsonRequest(
                url=url,
                headers={
                    "solo-concept": "cQhyxA8MVeI",
                    "accept-language": "ar-sa",
                },
                meta={"language": "ar"},
                dont_filter=True,
            )

    def post_process_item(self, item, response, location):
        item["branch"] = location["attributes"]["name"]
        item["lat"] = location["attributes"]["lat"]
        item["lon"] = location["attributes"]["long"]
        item["phone"] = location["attributes"]["telephone"]
        item["email"] = location["attributes"]["email"]
        item["addr_full"] = location["attributes"]["line1"]
        # item["country"] = location["attributes"]["country"] # Incorrect country (SA) reported for some locations
        apply_yes_no(Extras.DELIVERY, item, location["attributes"]["delivery-enabled"] == 1, False)
        apply_yes_no(Extras.DRIVE_THROUGH, item, location["attributes"]["is-drive-thru-enabled"], False)
        item["opening_hours"] = OpeningHours()
        if location["attributes"]["open-24-hours"]:
            item["opening_hours"] = "Mo-Su 00:00-24:00"
        else:
            for day in location["attributes"]["opening-hours"]:
                item["opening_hours"].add_range(DAYS[day["day"]], day["open"], day["closed"])

        if item["ref"] in self.stored_items:
            other_item = self.stored_items.pop(item["ref"])
            if response.meta["language"] == "en":
                yield get_merged_item({"en": item, "ar": other_item}, "ar")
            else:
                yield get_merged_item({"en": other_item, "ar": item}, "ar")
        else:
            self.stored_items[item["ref"]] = item
