import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class StBankSpider(scrapy.Spider):
    name = "st_bank"
    item_attributes = {"brand": "S&T Bank"}
    allowed_domains = ["stbank.com"]
    start_urls = ["https://www.stbank.com/page-data/locations/page-data.json"]

    def parse(self, response):
        for location in response.json()["result"]["pageContext"]["locationData"]:
            yield self.parse_location(location)

    def parse_location(self, location):
        hours = OpeningHours()
        for day, intervals in location["hours"].items():
            if "isClosed" in intervals:
                continue
            for interval in intervals["openIntervals"]:
                hours.add_range(day[:2].capitalize(), interval["start"], interval["end"])

        properties = {
            "lat": location["geocodedCoordinate"]["latitude"],
            "lon": location["geocodedCoordinate"]["longitude"],
            "ref": location["locationUri"],
            "name": location["meta"]["id"],
            "addr_full": location["address"]["line1"],
            "city": location["address"]["city"],
            "state": location["address"]["region"],
            "postcode": location["address"]["postalCode"],
            "country": location["address"]["countryCode"],
            "website": "https://www.stbank.com" + location["locationUri"],
            "phone": location["mainPhone"],
            "extras": {"fax": location.get("fax")},
            "opening_hours": hours.as_opening_hours(),
        }
        return Feature(**properties)
