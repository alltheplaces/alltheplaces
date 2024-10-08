from urllib.parse import urljoin

import scrapy

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.spiders.mcdonalds import McdonaldsSpider


class McdonaldsPLSpider(scrapy.Spider):
    name = "mcdonalds_pl"
    item_attributes = McdonaldsSpider.item_attributes
    allowed_domains = ["mcdonalds.pl"]

    start_urls = ["https://mcdonalds.pl/data/places"]

    def parse_hours(self, item, poi):
        if hours := poi.get("hours"):
            try:
                oh = OpeningHours()
                for day, time in hours.items():
                    if time.get("alwaysOpen") is True:
                        oh.add_range(DAYS[int(day) - 1], "00:00", "23:59")
                    else:
                        oh.add_range(DAYS[int(day) - 1], time.get("from"), time.get("to"))
                item["opening_hours"] = oh
            except:
                self.logger.warning(f"Failed to parse opening hours: {hours}")

    def parse(self, response):
        places = response.json().get("places")
        for poi in places:
            poi["street_address"] = poi.pop("address")
            item = DictParser.parse(poi)
            item["website"] = urljoin("https://mcdonalds.pl/restauracje/", poi["slug"])
            self.parse_hours(item, poi)
            apply_yes_no(Extras.WIFI, item, poi.get("wifi"))
            apply_yes_no(Extras.DELIVERY, item, poi.get("mcDelivery"))
            apply_yes_no(Extras.DRIVE_THROUGH, item, poi.get("mcDrive"))
            yield item
