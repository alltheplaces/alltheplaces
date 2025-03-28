import re

import scrapy

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.spiders.mcdonalds import McdonaldsSpider
from locations.user_agents import BROWSER_DEFAULT


class McdonaldsESSpider(scrapy.Spider):
    name = "mcdonalds_es"
    item_attributes = McdonaldsSpider.item_attributes
    custom_settings = {"ROBOTSTXT_OBEY": False}
    user_agent = BROWSER_DEFAULT
    start_urls = ["https://mcdonalds.es/api/restaurants?lat=36.721261&lng=-4.4212655&radius=500000000000&limit=10000"]

    def parse(self, response, **kwargs):
        name_re = re.compile(r"mc ?donald['´'`]?s", re.IGNORECASE)
        for location in response.json()["results"]:
            if location["open"] is True:
                # some locations are not open yet
                item = DictParser.parse(location)
                item["branch"] = name_re.sub("", item.pop("name")).strip()

                item["ref"] = location["site"]
                item["postcode"] = location["cp"]

                if "mccafe" in location["services"]:
                    mccafe = item.deepcopy()
                    mccafe["ref"] = "{}-mccafe".format(item["ref"])
                    mccafe["brand"] = "McCafé"
                    mccafe["brand_wikidata"] = "Q3114287"
                    apply_category(Categories.CAFE, mccafe)
                    yield mccafe

                self.parse_opening_hours(item, location["schedules"].get("restaurant"))

                apply_yes_no(Extras.DELIVERY, item, "delivery" in location["services"])
                apply_yes_no(Extras.TAKEAWAY, item, "takeaway" in location["services"])
                apply_yes_no(Extras.OUTDOOR_SEATING, item, "terrace" in location["services"])
                apply_yes_no(Extras.DRIVE_THROUGH, item, "mcauto" in location["services"])

                apply_category(Categories.FAST_FOOD, item)

                yield item

    def parse_opening_hours(self, item, data):
        if not data:
            return

        oh = OpeningHours()
        for day, times in data.items():
            if day != "festive":
                oh.add_range(day, times.get("start"), times.get("end"))

        item["opening_hours"] = oh
