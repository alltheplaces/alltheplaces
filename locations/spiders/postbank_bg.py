import re

import scrapy
from scrapy.http import FormRequest

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_BG, OpeningHours, day_range, sanitise_day
from locations.items import Feature


class PostbankBGSpider(scrapy.Spider):
    name = "postbank_bg"
    item_attributes = {"brand": "Postbank", "brand_wikidata": "Q7234083", "country": "BG"}
    allowed_domains = ["www.postbank.bg"]
    start_urls = ["https://www.postbank.bg/bg-BG/api/locations/locations"]
    no_refs = True

    def start_requests(self):
        return [
            FormRequest(
                "https://www.postbank.bg/bg-BG/api/locations/locations",
                formdata={"contextItemPath": "/sitecore/content/postbank/home"},
                callback=self.parse,
            )
        ]

    def parse(self, response):
        for city in response.json():
            for location in city["branches"]:
                # ignore temporarily closed locations
                if "временно" in location["worktime"].lower() or "временно" in location["address"].lower():
                    continue

                item = Feature()
                item["name"] = location["name"]
                item["addr_full"] = location["address"]
                item["lat"] = location["branchCoords"]["lat"]
                item["lon"] = location["branchCoords"]["lng"]
                item["phone"] = location["phone"]

                item["opening_hours"] = OpeningHours()

                if location["worktime"] is not None:
                    # ; needs to be replaced for a single item only..
                    for worktime in location["worktime"].replace(" : ", " ").replace(";", ":").split("<br/>"):
                        if worktime == "":
                            continue
                        match = re.match(r"([а-я]+\s?\-?\s?[а-я]+)+[\s:]+(\d{2}:\d{2})-(\d{2}:\d{2})", worktime.lower())
                        if match:
                            days = [sanitise_day(day, DAYS_BG) for day in match.group(1).replace(" ", "").split("-")]
                            hours = [match.group(2), match.group(3)]
                            if len(days) == 2:
                                item["opening_hours"].add_days_range(day_range(days[0], days[1]), hours[0], hours[1])
                            else:
                                item["opening_hours"].add_range(days[0], hours[0], hours[1])

                if location["isATM"]:
                    apply_category(Categories.ATM, item)
                    apply_yes_no(Extras.CASH_IN, item, location["isATMWithDeposit"])
                elif location["isBranch"]:
                    apply_category(Categories.BANK, item)
                    apply_yes_no("self_service", item, location["isSelfServiceZone"])
                yield item
