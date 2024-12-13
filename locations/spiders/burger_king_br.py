import scrapy
from scrapy.http import JsonRequest

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES

SERVICES_MAPPING = {
    "Drive Thru": Extras.DRIVE_THROUGH,
    "Delivery": Extras.DELIVERY,
}


class BurgerKingBRSpider(scrapy.Spider):
    name = "burger_king_br"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    allowed_domains = ["www.burgerking.com.br"]
    requires_proxy = True

    def start_requests(self):
        yield JsonRequest(
            url="https://www.burgerking.com.br/api/nearest",
            # We can get all POIs using any city from https://www.burgerking.com.br/api/cities
            data={"localization": {}, "address": "Americana", "nonParticipatingStores": ""},
        )

    def parse(self, response):
        for key, poi in response.json()["entries"].items():
            if key == "cacheForever":
                continue
            item = DictParser.parse(poi)
            item["state"] = poi["administrativeArea"]
            self.parse_hours(item, poi)
            self.parse_services(item, poi)
            yield item

    def parse_hours(self, item, poi):
        try:
            oh = OpeningHours()
            missing_weekdays = self.parse_regular_hours(poi, oh)
            self.parse_special_hours(poi, oh, missing_weekdays)
            item["opening_hours"] = oh.as_opening_hours()
        except Exception as e:
            self.logger.warning(f"Failed to parse hours: {e}, {poi}")

    def parse_regular_hours(self, poi, oh: OpeningHours):
        missing_weekdays = 0
        for key, value in poi.items():
            if key.endswith("Hours") and key != "specialHours":
                day = key[:-5]
                if "24h" in value:
                    oh.add_range(day, "00:00", "23:59")
                elif "N/A" not in value and "não abre" not in value.lower():
                    open, close = self.split_hours(value)
                    oh.add_range(day, open, close)
                else:
                    missing_weekdays += 1
        return missing_weekdays

    def parse_special_hours(self, poi, oh: OpeningHours, missing_weekdays):
        if missing_weekdays > 7 and "specialHours" in poi:
            value = poi["specialHours"]
            if "24h" in value:
                oh.add_days_range(DAYS, "00:00", "23:59")
            if "N/A" not in value and "não abre" not in value.lower():
                open, close = self.split_hours(value)
                oh.add_days_range(DAYS, open, close)

    def split_hours(self, value):
        open, close = value.split("-")
        return open.strip(), close.strip()

    def parse_services(self, item, poi):
        if services := poi.get("storeServices"):
            for service in services:
                title = service.get("title")
                if tag := SERVICES_MAPPING.get(title):
                    apply_yes_no(tag, item, True)
                else:
                    self.crawler.stats.inc_value(f"atp/burger_king_br/unknown_service/{title}")
