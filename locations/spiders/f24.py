from typing import Iterable

import chompjs
from scrapy.http import TextResponse

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
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
        if "https://test." in feature["stationPageUrl"]:
            return
        item["street_address"] = item.pop("street")
        item["branch"] = item.pop("name").split(",")[0]
        item["website"] = feature["stationPageUrl"]

        item["opening_hours"] = OpeningHours()
        for rule in ["Weekday", "Saturday", "Sunday"]:
            self.add_rule(item["opening_hours"], rule, feature.get(f"openHours{rule}"))

        if brand := self.BRANDS.get(feature["network"]):
            item.update(brand)

        apply_category(Categories.FUEL_STATION, item)

        services = [service["specificTag"] for service in feature.get("allServices", [])]
        apply_yes_no(Extras.CAR_WASH, item, any("CAR_WASH" in service for service in services))
        apply_yes_no(Fuel.OCTANE_95, item, "FUEL_GO_EASY_95" in services)
        apply_yes_no(Fuel.OCTANE_98, item, "FUEL_GO_EASY_98_EXTRA" in services)
        apply_yes_no(Fuel.BIODIESEL, item, "FUEL_DIESEL_BIO_HVO_100" in services)
        apply_yes_no(Fuel.ADBLUE, item, any("FUEL_AD_BLUE" in service for service in services))
        apply_yes_no(Fuel.DIESEL, item, any("FUEL_GO_EASY_DIESEL" in service for service in services))
        apply_yes_no(Fuel.ELECTRIC, item, any("CHARGE_QUICK_CHARGE" in service for service in services))

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
