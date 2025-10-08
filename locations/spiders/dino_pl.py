from typing import Iterable

import chompjs
from scrapy.http import Response

from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class DinoPLSpider(JSONBlobSpider):
    name = "dino_pl"
    item_attributes = {"brand": "Dino", "brand_wikidata": "Q11694239"}
    allowed_domains = ["marketdino.pl"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = ["https://marketdino.pl/map"]
    no_refs = True

    def extract_json(self, response: Response) -> list[dict]:
        return chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "mapData")]/text()').re_first(r"data[:\s]+(\[{.+}\]),")
        )[0]["mapData"]["features"]

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("properties"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name", "").strip().rsplit(" ", 1)[0]
        item["opening_hours"] = OpeningHours()
        try:
            if week_hours := feature.get("weekHours"):
                if ":" in week_hours:
                    item["opening_hours"].add_days_range(DAYS[:-1], *week_hours.split("-", 1))
            if sun_hours := feature.get("sundayHours"):
                if ":" in sun_hours:
                    item["opening_hours"].add_range("Su", *sun_hours.split("-", 1))
        except:
            self.logger.error(
                f'Failed to parse opening hours: Week Hours: {feature.get("weekHours")}, Sunday Hours: {feature.get("sundayHours")}'
            )
        yield item
