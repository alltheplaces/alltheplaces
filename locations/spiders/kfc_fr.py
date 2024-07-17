from scrapy.spiders import Spider

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import set_closed
from locations.spiders.kfc_us import KFC_SHARED_ATTRIBUTES
from locations.user_agents import FIREFOX_LATEST


class KfcFRSpider(Spider):
    name = "kfc_fr"
    item_attributes = KFC_SHARED_ATTRIBUTES
    start_urls = ["https://api.kfc.fr/stores/allStores"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    user_agent = FIREFOX_LATEST

    def parse(self, response, **kwargs):
        for location in response.json():
            item = DictParser.parse(location)
            item["branch"] = item.pop("name").removeprefix("KFC ")
            item["website"] = "https://www.kfc.fr/nos-restaurants/{}".format(location["url"])
            item["extras"]["ref:google"] = location["placeId"]

            apply_yes_no(Extras.DELIVERY, item, "delivery" in location["dispositions"])
            apply_yes_no(Extras.TAKEAWAY, item, "pickup" in location["dispositions"])
            apply_yes_no(Extras.WIFI, item, location["services"]["serviceSurPlace"]["freewifi"])

            if location["status"] == "SHUTDOWN":
                set_closed(item)
            else:
                item["opening_hours"] = self.parse_hours(location["operatingHours"])
                item["extras"]["opening_hours:drive_through"] = self.parse_hours(location["driveThruOperatingHours"])

            yield item

    def parse_hours(self, hours: list) -> str:
        opening_hours = OpeningHours()
        for rule in hours:
            day = DAYS[rule["dayOfWeek"] - 1]
            opening_hours.add_range(
                day, rule["start"], rule["end"], time_format="%H:%M" if len(rule["end"]) == 5 else "%H:%M:%S"
            )
        return opening_hours.as_opening_hours()
