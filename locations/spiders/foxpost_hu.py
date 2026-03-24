from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, PaymentMethods, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_HU, OpeningHours, sanitise_day


class FoxpostHUSpider(Spider):
    name = "foxpost_hu"
    item_attributes = {"brand": "Foxpost", "brand_wikidata": "Q126538316"}
    start_urls = ["https://cdn.foxpost.hu/apt-finder/v1/app/markers.php?lang=hu&c2c=1&show_prod_zboxes=1"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["list"]:
            item = DictParser.parse(location)
            item["street_address"] = item.pop("street")
            item["ref"] = location["operator_id"].upper()

            try:
                item["opening_hours"] = self.parse_opening_hours(location["open"])
            except:
                self.logger.error("Error parsing opening hours: {}".format(location["open"]))

            apply_category(Categories.PARCEL_LOCKER, item)

            apply_yes_no(PaymentMethods.CASH, item, location["cashPayment"] is True)
            apply_yes_no(PaymentMethods.CARDS, item, "card" in location["paymentOptions"])

            yield item

    def parse_opening_hours(self, open: dict) -> OpeningHours:
        oh = OpeningHours()

        for day, times in open.items():
            if times != "-":
                start_time, end_time = times.split("-")
                oh.add_range(sanitise_day(day, DAYS_HU), start_time.strip(), end_time.strip())

        return oh
