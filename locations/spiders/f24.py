import re
from typing import Iterable

import chompjs
from scrapy.http import TextResponse

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
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
        chunks = []
        for script in response.xpath('//script[contains(text(), "self.__next_f.push")]/text()').getall():
            if m := re.search(r"self\.__next_f\.push\((.*)\)\s*$", script, re.DOTALL):
                payload = chompjs.parse_js_object(m.group(1))
                if len(payload) == 2 and isinstance(payload[1], str):
                    chunks.append(payload[1])
        data = "".join(chunks)

        marker = '"stations":'
        start = data.find(marker + "[")
        if start == -1:
            return []
        return chompjs.parse_js_object(data[start + len(marker) :])

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if "test." in feature["stationPageUrl"]:
            return

        item["street_address"] = item.pop("street", None)
        item["branch"] = item.pop("name").split(",")[0]
        item["website"] = response.urljoin(feature["stationPageUrl"])

        item["opening_hours"] = OpeningHours()
        for rule in ["Weekday", "Saturday", "Sunday"]:
            self.add_rule(item["opening_hours"], rule, feature.get(f"openHours{rule}") or {})

        if brand := self.BRANDS.get(feature["network"]):
            item.update(brand)

        apply_category(Categories.FUEL_STATION, item)

        tags = feature.get("genericTags", [])
        apply_yes_no(Extras.CAR_WASH, item, "WASH" in tags)
        apply_yes_no(Fuel.ELECTRIC, item, "CHARGE" in tags)

        yield item

    @staticmethod
    def add_rule(oh: OpeningHours, day: str, rule: dict) -> None:
        if rule.get("open") and rule.get("close"):
            open_time, close_time = [hours.replace(".", ":") for hours in [rule["open"], rule["close"]]]
            close_time = close_time.replace("00:00", "23:59")
            if day == "Weekday":
                oh.add_days_range(DAYS[:5], open_time, close_time)
            else:
                oh.add_range(day, open_time, close_time)
