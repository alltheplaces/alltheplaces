from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.spiders.mcdonalds import McdonaldsSpider


class McdonaldsLatinAmericaSpider(Spider):
    name = "mcdonalds_latin_america"
    item_attributes = McdonaldsSpider.item_attributes
    allowed_domains = ["api-middleware-mcd.mcdonaldscupones.com"]
    start_urls = ["https://api-middleware-mcd.mcdonaldscupones.com/api/restaurant/list"]
    country_codes = [
        "AR",
        "BR",
        "CL",
        "CO",
        "CR",
        "EC",
        "GF",
        "GP",
        "MQ",
        "MX",
        "PA",
        "PE",
        "PR",
        "UY",
        "VE",
    ]

    def start_requests(self):
        for country_code in self.country_codes:
            yield JsonRequest(url=self.start_urls[0], headers={"x-app-country": country_code}, dont_filter=True)

    def parse(self, response):
        if not response.json().get("status"):
            return

        for location in response.json().get("data"):
            if not location["active"]:
                continue

            item = DictParser.parse(location)
            item["ref"] = location["code"]
            if location["country"] in ["AR", "PR"]:
                item["addr_full"] = location["address"]
                item.pop("street_address", None)
            else:
                item["street_address"] = location["address"]
                item.pop("addr_full", None)

            if location.get("generalHour"):
                item["opening_hours"] = OpeningHours()
                for day_hours in location["generalHour"]["daysOfWeek"]:
                    for time_period in day_hours["timePeriods"]:
                        item["opening_hours"].add_range(
                            day_hours["day"].title(), time_period["start"], time_period["end"]
                        )

            apply_yes_no(Extras.DRIVE_THROUGH, item, location["services"]["driveThru"], False)
            apply_yes_no(Extras.DELIVERY, item, location["services"]["mcDelivery"], False)
            apply_yes_no(Extras.WIFI, item, location["services"]["wifi"], False)
            apply_yes_no(Extras.WHEELCHAIR, item, location["services"]["wheelchairAccess"], False)

            apply_category(Categories.FAST_FOOD, item)

            yield item
