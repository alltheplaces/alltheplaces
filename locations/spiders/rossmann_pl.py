from scrapy import Spider
import re

from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature


class RossmannPLSpider(Spider):
    name = "rossmann_pl"
    item_attributes = {"brand": "Rossmann", "brand_wikidata": "Q316004"}
    start_urls = ["https://www.rossmann.pl/shops/api/Shops"]

    def parse(self, response):
        data = response.json()["data"]

        regex = r"(\S+\.?) ([\S ]+) (\d+ ?[a-zA-Z]?)"
        pattern = re.compile(regex)

        for shop in data:

            hours = self.parse_hours(shop.get("openHours"))

            matcher = re.match(regex, shop["address"]["street"].replace("\r\n", ""))
            street = matcher.group(2) if matcher != None else ""
            housenumber = matcher.group(3) if matcher != None else ""

            properties = {
                "ref": shop["shopNumber"],
                "street_address": shop["address"]["street"].replace("\r\n", ""),
                "street": street,
                "housenumber": housenumber,
                "city": shop["address"]["city"],
                "postcode": shop["address"]["postCode"],
                "country": "PL",
                "opening_hours": hours.as_opening_hours(),
                "lat": shop["shopLocation"]["latitude"],
                "lon": shop["shopLocation"]["longitude"],
                "website": "https://www.rossmann.pl/drogerie" + shop["navigateUrlV2"],
            }

            item = Feature(**properties)

            yield item

    def parse_hours(self, data):

        hours = OpeningHours()
        for day in [x.lower() for x in DAYS_FULL]:
            if day + "OpenFrom" not in data:
                continue
            start_time = data[day + "OpenFrom"]
            end_time = data[day + "OpenTo"]
            hours.add_range(day[:2].capitalize(), start_time, end_time, "%H:%M")

        return hours
