from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class GeneralPantsCoSpider(Spider):
    name = "general_pants_co"
    item_attributes = {"brand": "General Pants Co", "brand_wikidata": "Q5532086"}
    allowed_domains = ["www.generalpants.com"]
    start_urls = [
        "https://www.generalpants.com/au/store-finder-rest/",
        "https://www.generalpants.com/nz/store-finder-rest/",
    ]
    # Requesting robots.txt will cause server-side IP geolocation to
    # redirect to a localised generalpants.com sub-site for a
    # different country than that requested. This breaks the country
    # specification in the API request. Thus robots.txt should not be
    # requested (even if it does not contain a rule blocking this
    # spider).
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["results"]:
            if "Online" in location["name"].title() or location["address"]["state"].title() == "Online":
                continue
            if not location["openFlag"]:
                continue
            item = DictParser.parse(location)
            item["ref"] = location["code"]
            item["street_address"] = ", ".join(
                filter(None, [location["address"]["line1"], location["address"]["line2"]])
            )
            item["addr_full"] = location["address"]["formattedAddress"]
            item["phone"] = location["address"].get("phone")
            item["email"] = location["address"].get("email")
            item["website"] = (
                "https://www.generalpants.com/"
                + location["address"]["country"]["isocode"].lower()
                + "/store/"
                + location["nameClean"]
            )
            if location.get("openingHours"):
                item["opening_hours"] = OpeningHours()
                for day_hours in location["openingHours"]["weekDayOpeningList"]:
                    if day_hours["closed"]:
                        continue
                    item["opening_hours"].add_range(
                        day_hours["weekDay"],
                        day_hours["openingTime"]["formattedHour"].upper(),
                        day_hours["closingTime"]["formattedHour"].upper(),
                        "%I:%M %p",
                    )
            yield item
