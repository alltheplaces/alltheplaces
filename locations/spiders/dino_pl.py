from typing import Iterable

from scrapy.http import Response

from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class DinoPLSpider(JSONBlobSpider):
    name = "dino_pl"
    item_attributes = {"brand": "Dino", "brand_wikidata": "Q11694239"}
    allowed_domains = ["marketdino.pl"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = ["https://marketdino.pl/map/_payload.json"]
    no_refs = True

    def extract_json(self, response: Response) -> list:
        payload = response.json()

        def is_populateable(v) -> bool:
            return isinstance(v, int) and 0 < v < len(payload)

        def populate(index: int):
            val = payload[index]
            if isinstance(val, dict):
                for k, v in val.items():
                    if is_populateable(v):
                        val[k] = populate(v)
            elif isinstance(val, list):
                for i in range(0, len(val)):
                    if is_populateable(val[i]):
                        val[i] = populate(val[i])
            elif isinstance(val, dict):
                for k, v in val.items():
                    if is_populateable(v):
                        val[k] = payload[v]
            return val

        return [
            v["properties"]
            | {
                "lon": v["geometry"]["coordinates"][0],
                "lat": v["geometry"]["coordinates"][1],
            }
            for v in populate(0)["data"][1]["map-data"]["features"]
        ]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name", "").strip().rsplit(" ", 1)[0]
        item["opening_hours"] = OpeningHours()
        try:
            day_hours_map = {
                "mondayHours": "Mo",
                "tuesdayHours": "Tu",
                "wednesdayHours": "We",
                "thursdayHours": "Th",
                "fridayHours": "Fr",
                "saturdayHours": "Sa",
                "sundayHours": "Su",
            }
            for day_key, osm_day in day_hours_map.items():
                if hours := feature.get(day_key):
                    if ":" in hours:
                        try:
                            start, end = hours.split("-", 1)
                            item["opening_hours"].add_range(osm_day, start.strip(), end.strip())
                        except Exception as e:
                            self.logger.warning(f"Failed to parse {day_key}: {hours} - {e}")
        except Exception as e:
            self.logger.error(f"Failed to parse opening hours: {e}")

        yield item
