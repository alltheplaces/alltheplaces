from scrapy.http import Response

from locations.categories import Extras, apply_yes_no
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class WhiteCastleSpider(JSONBlobSpider):
    name = "white_castle"
    item_attributes = {"brand": "White Castle", "brand_wikidata": "Q1244034"}
    start_urls = ["https://www.whitecastle.com/api/vtl/get-nearest-location?lat=0&long=0distance=25000&count=1000"]
    locations_key = "results"

    def pre_process_data(self, store: dict, **kwargs):
        store["ref"] = store.get("storeNumber")
        store["street_address"] = store.pop("address")
        store.pop("name")

    def post_process_item(self, item: Feature, response: Response, store: dict, **kwargs):
        item["website"] = f'https://www.whitecastle.com/locations/{store.get("storeNumber")}'

        delivery_options = store.get("deliveryOptions") or {}
        if delivery_options:
            item["extras"]["delivery:partner"] = ";".join(delivery_options.keys())
        apply_yes_no(Extras.DELIVERY, item, bool(delivery_options))

        item["opening_hours"] = self.parse_opening_hours(store)

        yield item

    def parse_opening_hours(self, store: dict) -> OpeningHours:
        oh = OpeningHours()
        for day in DAYS_FULL:
            value = (store.get(f"{day.lower()}Hours") or "").strip()
            if not value:
                continue
            if "24 hr" in value.lower():
                oh.add_range(day, "00:00", "23:59")
                continue
            if "-" not in value:
                continue

            open_time, _, close_time = value.partition("-")
            open_time = " ".join(open_time.upper().replace("AM", " AM").replace("PM", " PM").split())
            close_time = " ".join(close_time.upper().replace("AM", " AM").replace("PM", " PM").split())

            oh.add_range(day, open_time, close_time, time_format="%I:%M %p")

        return oh
