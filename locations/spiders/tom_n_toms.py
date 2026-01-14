from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class TomNTomsSpider(JSONBlobSpider):
    name = "tom_n_toms"
    item_attributes = {"brand": "Tom N Toms", "brand_wikidata": "Q18142418"}
    start_urls = ["https://www.tomntoms.com/api/v1/store/domestic", "https://www.tomntoms.com/api/v1/store/overseas"]
    locations_key = ["data", "elements"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["lat"] = feature.get("point_x")
        item["lon"] = feature.get("point_y")
        item["addr_full"] = feature.get("roadAddress")
        open_time, close_time = feature.get("startTime", "").strip(), feature.get("endTime", "").strip()
        if open_time and close_time:
            open_time, close_time = [t.replace(":0", ":00") if t.endswith(":0") else t for t in [open_time, close_time]]
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_days_range(DAYS, open_time, close_time)
        apply_category(Categories.CAFE, item)
        if services := feature.get("services"):
            service_ids = [service["id"] for service in services]
            apply_yes_no(Extras.WIFI, item, 3 in service_ids)
            apply_yes_no(Extras.OUTDOOR_SEATING, item, 5 in service_ids)
            apply_yes_no(Extras.DRIVE_THROUGH, item, 9 in service_ids)
            apply_yes_no(Extras.DELIVERY, item, 11 in service_ids)
        yield item
