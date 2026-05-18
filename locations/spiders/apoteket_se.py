from scrapy.http import Response

from locations.hours import DAYS_SE, OpeningHours, sanitise_day
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class ApoteketSESpider(JSONBlobSpider):
    name = "apoteket_se"
    item_attributes = {"brand": "Apoteket", "brand_wikidata": "Q17047215"}
    start_urls = ["https://www.apoteket.se/bff/v1/pharmacies/all"]

    def pre_process_data(self, data: dict, **kwargs):
        data["street-address"] = data.pop("address", None)

    def post_process_item(self, item: Feature, response: Response, feature: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Apoteket ").strip()

        if url_path := feature.get("url"):
            item["website"] = response.urljoin(url_path)

        item["opening_hours"] = self.parse_opening_hours(feature.get("openingHours") or [])

        yield item

    def parse_opening_hours(self, opening_hours: list[dict]) -> OpeningHours:
        oh = OpeningHours()
        for entry in opening_hours:
            day = sanitise_day(entry.get("day"), DAYS_SE)
            if not day:
                continue
            open_time = entry.get("openTime")
            close_time = entry.get("closeTime")
            if not open_time or not close_time:
                oh.set_closed(day)
                continue
            break_start = entry.get("breakStart")
            break_end = entry.get("breakEnd")
            if break_start and break_end:
                oh.add_range(day, open_time, break_start)
                oh.add_range(day, break_end, close_time)
            else:
                oh.add_range(day, open_time, close_time)
        return oh
