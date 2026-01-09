from typing import Iterable

import chompjs
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.q8_italia import Q8ItaliaSpider


class F24Spider(JSONBlobSpider):
    name = "f24"
    start_urls = ["https://www.f24.dk/find-station/"]
    BRANDS = {
        "F24": {"brand": "F24", "brand_wikidata": "Q12310853"},
        "Q8": Q8ItaliaSpider.item_attributes,
    }

    def extract_json(self, response: TextResponse) -> list[dict]:
        return DictParser.get_nested_key(
            chompjs.parse_js_object(
                response.xpath('//script[contains(text(), "window.__APP_INIT_DATA__")]/text()').get()
            ),
            "stations",
        )

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["street_address"] = item.pop("street")
        item["website"] = feature["stationPageUrl"]

        if feature.get("openingHours"):
            if feature["openingHours"]["AlwaysOpen"]:
                item["opening_hours"] = "24/7"
            else:
                item["opening_hours"] = OpeningHours()
                for rule in ["WeekDays", "Saturday", "Sunday"]:
                    self.add_rule(item["opening_hours"], rule, feature["openingHours"].get(rule))

        if brand := self.BRANDS.get(feature["network"]):
            item.update(brand)

        apply_category(Categories.FUEL_STATION, item)

        yield item

    @staticmethod
    def add_rule(oh: OpeningHours, day: str, rule: dict):
        if rule.get("Closed"):
            return
        if day == "WeekDays":
            oh.add_days_range(DAYS[:5], rule["From"], rule["To"])
        else:
            oh.add_range(day, rule["From"], rule["To"])
