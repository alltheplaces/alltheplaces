import re

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class EngelAndVolkersSpider(Spider):
    name = "engel_and_volkers"
    item_attributes = {"brand": "Engel & Völkers", "brand_wikidata": "Q1341765"}
    allowed_domains = ["engelvoelkers.com"]
    search_url_template = "https://shop-finder-backend.engelvoelkers.com/shop-finder/search?page=1&limit=10000&lat=0&lng=0&boundingBox=0,0,0,0&businessUnit=BOTH&city=&location=&country={country_code}&newSearchLogic=true"
    country_codes = [
        "AD",
        "AE",
        "AT",
        "BE",
        "BS",
        "CA",
        "CH",
        "CL",
        "CO",
        "CR",
        "CZ",
        "DE",
        "DK",
        "ES",
        "FR",
        "GR",
        "HR",
        "HU",
        "IE",
        "IT",
        "KY",
        "LI",
        "LU",
        "MX",
        "NL",
        "PT",
        "TC",
        "US",
        "ZA",
    ]

    def start_requests(self):
        for country_code in self.country_codes:
            yield JsonRequest(url=self.search_url_template.format(country_code=country_code))

    def parse(self, response):
        for location in response.json()["shops"]:
            if location["status"] != "OPENED":
                continue
            item = DictParser.parse(location)
            item["lat"] = location["address"]["location"].get("lat")
            item["lon"] = location["address"]["location"].get("lng")
            item["street_address"] = item.pop("street", None)
            item["city"] = location["address"].get("city")
            item["country"] = location["address"].get("countryCode")
            item["postcode"] = location["address"].get("postalCode")
            item["phone"] = location["contactInfo"].get("phone")
            item["website"] = location["contactInfo"].get("website")
            if item["website"]:
                item["website"] = re.sub(r"^engelvoelkers\.com\/", "https://engelvoelkers.com/", item["website"])
                item["website"] = re.sub(
                    r"^www\.engelvoelkers\.com\/", "https://www.engelvoelkers.com/", item["website"]
                )
                item["website"] = re.sub(
                    r"^([\w\-]+)\.evrealestate\.com", r"https://\1.evrealestate.com", item["website"]
                )
            if location.get("googlePlaceDetails") and location["googlePlaceDetails"].get("openingHours"):
                item["opening_hours"] = OpeningHours()
                for day_hours in location["googlePlaceDetails"]["openingHours"]["periods"]:
                    if not day_hours.get("open") or not day_hours.get("close"):
                        continue
                    item["opening_hours"].add_range(
                        DAYS[day_hours["open"]["day"] - 1],
                        day_hours["open"]["time"],
                        day_hours["close"]["time"],
                        "%H%M",
                    )
            yield item
