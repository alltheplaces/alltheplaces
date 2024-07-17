from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.pipelines.address_clean_up import clean_address


class URBNSpider(Spider):
    name = "urbn"
    allowed_domains = ["www.anthropologie.com"]
    start_urls = ["https://www.anthropologie.com/api/misl/v1/stores/search"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    brands = {
        "ANTHROPOLOGIE": {
            "brand": "Anthropologie",
            "brand_wikidata": "Q4773903",
            "website": "https://www.anthropologie.com/stores/{slug}",
        },
        "ANTHROPOLOGIE EU": {
            "brand": "Anthropologie",
            "brand_wikidata": "Q4773903",
            "website": "https://www.anthropologie.com/stores/{slug}",
        },
        "FREE PEOPLE": {
            "brand": "Free People",
            "brand_wikidata": "Q5499945",
            "website": "https://www.freepeople.com/stores/{slug}",
        },
        "FREE PEOPLE UK EU": {
            "brand": "Free People",
            "brand_wikidata": "Q5499945",
            "website": "https://www.freepeople.com/stores/{slug}",
        },
        "URBAN OUTFITTERS": {
            "brand": "Urban Outfitters",
            "brand_wikidata": "Q3552193",
            "website": "https://www.urbanoutfitters.com/stores/{slug}",
        },
        "URBAN OUTFITTERS EU": {
            "brand": "Urban Outfitters",
            "brand_wikidata": "Q3552193",
            "website": "https://www.urbanoutfitters.com/stores/{slug}",
        },
    }

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["results"]:
            if location.get("closed") is True:
                continue
            item = DictParser.parse(location)
            if location["brandName"] in self.brands:
                item.update(self.brands[location["brandName"]])
            else:
                continue
            item["ref"] = str(location["number"])
            item["name"] = location["addresses"]["marketing"].get("name")
            if "COMING SOON" in item["name"].upper() or "CLOSED" in item["name"].upper().split():
                continue
            item["street_address"] = clean_address(
                [
                    location["addresses"]["marketing"].get("addressLineOne"),
                    location["addresses"]["marketing"].get("addressLineTwo"),
                ]
            )
            item["city"] = location["addresses"]["marketing"].get("city")
            item["state"] = location["addresses"]["marketing"].get("state")
            item["postcode"] = location["addresses"]["marketing"].get("postcode")
            item["lat"] = location["loc"][1]
            item["lon"] = location["loc"][0]
            if location.get("slug"):
                item["website"] = item["website"].format(slug=location["slug"])
            else:
                item.pop("website")
            if location.get("storePhoneNumber") and "?" not in location.get("storePhoneNumber"):
                item["phone"] = location["storePhoneNumber"]
            elif location["addresses"]["marketing"].get("phoneNumber") and "?" not in location["addresses"][
                "marketing"
            ].get("phoneNumber"):
                item["phone"] = location["addresses"]["marketing"]["phoneNumber"]
            item["opening_hours"] = OpeningHours()
            hours_string = ""
            for day_number, day_hours in location["hours"].items():
                hours_string = (
                    hours_string + " " + DAYS[int(day_number) - 1] + ": " + day_hours["open"] + "-" + day_hours["close"]
                )
            item["opening_hours"].add_ranges_from_string(hours_string)
            yield item
