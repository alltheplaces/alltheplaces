from typing import Iterable

from scrapy.http import Response

from locations.hours import DAYS_FULL, OpeningHours
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

        try:
            item["opening_hours"] = self.parse_opening_hours(feature)
        except Exception as e:
            self.logger.error(f"Failed to parse opening hours: {e}")

        yield item

    def parse_opening_hours(self, feature: dict) -> OpeningHours:
        oh = OpeningHours()
        for day in DAYS_FULL:
            if times := feature.get("{}Hours".format(day.lower())):
                if times == "nieczynne":
                    oh.set_closed(day)
                else:
                    oh.add_range(day, *times.split("-"))
        return oh
