

from locations.hours import DAYS_3_LETTERS, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class MenkindGBSpider(JSONBlobSpider):
    name = "menkind_gb"
    item_attributes = {"brand": "Menkind", "brand_wikidata": "Q66725844"}
    start_urls = ["https://storerocket.io/api/user/VyJzzwEJ6M/locations?radius=350&units=miles"]
    locations_key = ["results", "locations"]

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name").replace("MENKIND", "").strip()
        item["opening_hours"] = OpeningHours()
        for day in DAYS_3_LETTERS:
            hours = location.get("hours").get(day.lower())
            if hours and "-" in hours:
                open_time, close_time = (t.strip() for t in hours.split("-", 1))
                item["opening_hours"].add_range(day, open_time, close_time)
        yield item
