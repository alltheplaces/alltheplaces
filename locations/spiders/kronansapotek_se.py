from scrapy.http import Response

from locations.hours import DAYS_EN, OpeningHours, sanitise_day
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class KronansapotekSESpider(JSONBlobSpider):
    name = "kronansapotek_se"
    item_attributes = {"brand": "Kronans Apotek", "brand_wikidata": "Q10549422"}
    start_urls = ["https://web-api.kronansapotek.se/bizniz/public/pharmacy/search?page=0&pageSize=1000"]

    def extract_json(self, response):
        return [entry["pharmacy"] for entry in response.json()["pharmacies"]]

    def pre_process_data(self, feature: dict, **kwargs) -> None:
        feature["street-address"] = feature.pop("visitingAddress", None)
        feature["postcode"] = feature.pop("postalCode", None)
        feature["phone"] = feature.pop("phoneNumber", None)

    def post_process_item(self, item: Feature, response: Response, feature: dict, **kwargs):
        item["branch"] = item.pop("name", None)
        item["state"] = None
        item["opening_hours"] = self.parse_opening_hours(feature.get("regularSchedule") or [])
        yield item

    def parse_opening_hours(self, schedule: list[dict]) -> OpeningHours:
        oh = OpeningHours()
        for entry in schedule:
            day = sanitise_day(entry.get("weekday"), DAYS_EN)
            if not day:
                continue
            open_time = (entry.get("openTime") or "")[:5]
            close_time = (entry.get("closeTime") or "")[:5]
            if not open_time or not close_time:
                oh.set_closed(day)
                continue
            lunch_start = (entry.get("lunchStart") or "")[:5]
            lunch_stop = (entry.get("lunchStop") or "")[:5]
            if lunch_start and lunch_stop:
                oh.add_range(day, open_time, lunch_start)
                oh.add_range(day, lunch_stop, close_time)
            else:
                oh.add_range(day, open_time, close_time)
        return oh
