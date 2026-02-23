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

        def parse_feature(raw):
            coords = payload[payload[raw["geometry"]]["coordinates"]]
            return {k: payload[v] if isinstance(v, int) else v for k, v in payload[raw["properties"]].items()} | {
                "lon": coords[0],
                "lat": coords[1],
            }

        return [parse_feature(payload[idx]) for idx in payload[6]]

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
