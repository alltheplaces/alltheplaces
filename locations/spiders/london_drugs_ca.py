import json

import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class LondonDrugsCASpider(scrapy.Spider):
    name = "london_drugs_ca"
    item_attributes = {"brand": "London Drugs", "brand_wikidata": "Q3258955"}
    allowed_domains = ["www.londondrugs.com"]
    start_urls = ["https://www.londondrugs.com/on/demandware.store/Sites-LondonDrugs-Site/default/MktStoreList-All"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        stores = json.loads(response.body)
        for store in stores:
            item = DictParser.parse(store)
            item["image"] = "https://londondrugs.com" + store["image"]["url"]
            item["website"] = (
                "https://londondrugs.com/london-drugs-store-"
                + item["ref"]
                + "-"
                + item["city"].lower()
                + "/"
                + store["cityAliases"][0]
                + ".html"
            )
            for hours_type in store["storeHours"]:
                if hours_type["type"] == "Store Hours":
                    oh = OpeningHours()
                    hours_parsing_error = False
                    for day_range in hours_type["storeHours"]:
                        days = []
                        match day_range["day"]:
                            case "Mon-Fri":
                                days = ["Mo", "Tu", "We", "Th", "Fr"]
                            case "Mon-Sat":
                                days = ["Mo", "Tu", "We", "Th", "Fr", "Sa"]
                            case "Mon-Sun":
                                days = ["Mo", "Tu", "We", "Th", "Fr", "Sa"]
                            case "Wed-Fri":
                                days = ["We", "Fr"]
                            case "Sat-Sun" | "Sat - Sun":
                                days = ["Sa", "Su"]
                            case "Mon, Tues":
                                days = ["Mo", "Tu"]
                            case "Mon, Tues, Sat":
                                days = ["Mo", "Tu", "Sa"]
                            case "Mon,Wed,Fri":
                                days = ["Mo", "We", "Fr"]
                            case "Tue,Thu,Sat":
                                days = ["Tu", "Th", "Sa"]
                            case "Sat-Sun" | "Sat & Sun" | "Sat, Sun & Holidays":
                                days = ["Sa", "Su"]
                            case "Saturday" | "Sat":
                                days = ["Sa"]
                            case "Sunday" | "Sunday & Holidays" | "Sunday  & Holidays" | " Sunday  & Holidays" | "Sun & Holidays":
                                days = ["Su"]
                            case "Holidays":
                                days = []
                            case _:
                                hours_parsing_error = True
                        for day in days:
                            oh.add_range(day, day_range["hours"][0], day_range["hours"][1], "%I:%M %p")
                    if not hours_parsing_error:
                        item["opening_hours"] = oh.as_opening_hours()
            yield item
