import json
from typing import Iterable

from scrapy.http import Response

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class CavaUSSpider(JSONBlobSpider):
    name = "cava_us"
    item_attributes = {"brand": "CAVA", "brand_wikidata": "Q85751038"}
    start_urls = ["https://cava.com/locations"]

    def extract_json(self, response: Response) -> list[dict]:
        return DictParser.get_nested_key(
            json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()), "stores"
        )

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("geographic", {}))
        feature.update(feature.pop("address", {}))
        feature["address"] = feature.pop("primary", {})
        feature.update(feature.pop("communication", {}))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature.get("storeNumber")
        item["branch"] = item.pop("name")
        item["phone"] = feature.get("telephones", {}).get("primary", {}).get("number")
        item["email"] = feature.get("emailAddresses", {}).get("primary", {}).get("address")
        item["website"] = f'{response.url}/{feature.get("locationRef")}'
        hours_list = feature.get("channels", {}).get("nonChannel", {}).get("storeStoreHours", {}).get("hours") or [{}]
        try:
            item["opening_hours"] = self.parse_opening_hours(hours_list[0])
        except:
            self.logger.error(f"Failed to parse opening hours: {hours_list[0]}")

        services = feature.get("channels", {}).get("fulfillment") or {}
        apply_yes_no(Extras.DRIVE_THROUGH, item, "pickUpByCar" in services)
        apply_yes_no(Extras.INDOOR_SEATING, item, "dineInDineIn" in services)
        apply_yes_no(Extras.TAKEAWAY, item, "pickUpCarryOut" in services)
        yield item

    def parse_opening_hours(self, opening_hours: dict) -> OpeningHours:
        oh = OpeningHours()
        for day in DAYS_FULL:
            if hours := opening_hours.get(day.lower()):
                oh.add_range(day, hours["open"], hours["close"])
        return oh
