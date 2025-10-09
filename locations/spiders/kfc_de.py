from typing import Any

import chompjs
from scrapy.http import Response

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.spiders.kfc_us import KFC_SHARED_ATTRIBUTES
from locations.user_agents import FIREFOX_LATEST

SERVICES_MAPPING = {
    "click_collect": Extras.TAKEAWAY,
    "delivery": Extras.DELIVERY,
    "drivethru": Extras.DRIVE_THROUGH,
    "ec_cash": None,
    "free_refill": None,
}


class KfcDESpider(PlaywrightSpider):
    name = "kfc_de"
    item_attributes = KFC_SHARED_ATTRIBUTES
    start_urls = ["https://api.kfc.de/find-a-kfc/allrestaurant"]
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": FIREFOX_LATEST} | DEFAULT_PLAYWRIGHT_SETTINGS

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in chompjs.parse_js_object(response.text):
            if location["name"].endswith(" - COMING SOON"):
                continue
            location["street_address"] = location.pop("address")
            item = DictParser.parse(location)
            item["name"] = None
            item["ref"] = location["id"]
            item["website"] = "https://www.kfc.de/find-a-kfc/" + location["urlName"]
            oh = OpeningHours()
            opening_hour = location["operatingHoursStore"]
            for rule in opening_hour:
                if "dinein" in rule["disposition"]:
                    oh.add_range(DAYS[rule["dayOfWeek"]], rule["start"], rule["end"], time_format="%H:%M")
            item["opening_hours"] = oh.as_opening_hours()

            for service in location.get("services", []):
                if tags := SERVICES_MAPPING.get(service):
                    apply_yes_no(tags, item, True, True)
                else:
                    self.logger.warning(f"Unknown service {service}")

            apply_yes_no(Extras.INDOOR_SEATING, item, "dinein" in location["dispositions"])
            yield item
