from scrapy import Spider
from scrapy.http import FormRequest, JsonRequest

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class BuildersSpider(Spider):
    name = "builders"
    item_attributes = {"brand": "Builders", "brand_wikidata": "Q116819137", "extras": Categories.SHOP_HARDWARE.value}
    allowed_domains = ["www.builders.co.za"]
    start_urls = [
        "https://www.builders.co.za/web/v2/builders/channel/web/zone/B14/stores?query=&latitude=-26.1328705&longitude=27.9114834&radius=10000000&fields=FULL"
    ]

    def start_requests(self):
        formdata = {
            "client_id": "builders",
            # client_secret appears to be obfuscated within main.???.js and
            # does not appear to be easy to extract automatically.
            "client_secret": "Gh6tuc6L",
            "grant_type": "client_credentials",
        }
        yield FormRequest(
            url="https://www.builders.co.za/authorizationserver/oauth/token",
            method="POST",
            formdata=formdata,
            callback=self.parse_auth_token,
        )

    def parse_auth_token(self, response):
        auth_token = response.json()["access_token"]
        for url in self.start_urls:
            yield JsonRequest(url=url, headers={"Authorization": f"Bearer {auth_token}"}, callback=self.parse_locations)

    def parse_locations(self, response):
        for location in response.json()["stores"]:
            if location["type"] != "STORE":
                continue

            item = DictParser.parse(location)

            if not location.get("displayName") or "BUILDERS WAREHOUSE " in location["displayName"].upper():
                item["brand"] = "Builders Warehouse"
                item["name"] = location.get("displayName", "").replace("Builders Warehouse ", "")
            elif "BUILDERS EXPRESS " in location["displayName"].upper():
                item["brand"] = "Builders Express"
                item["name"] = location["displayName"].replace("Builders Express ", "")
            elif "BUILDERS SUPERSTORE " in location["displayName"].upper():
                item["brand"] = "Builders SuperStore"
                item["name"] = (
                    location["displayName"].replace("Builders SuperStore ", "").replace("Builders Superstore", "")
                )
            elif "BUILDERS TRADE DEPOT " in location["displayName"].upper():
                item["brand"] = "Builders Trade Depot"
                item["name"] = location["displayName"].replace("Builders Trade Depot ", "")
            else:
                self.logger.warning("Unknown brand from location name: {}".format(location["displayName"]))
                continue

            item["ref"] = location["name"]
            item.pop("street_address", None)
            item["addr_full"] = location["address"]["formattedAddress"]
            item["state"] = location["address"]["region"]["name"]
            item.pop("website", None)

            item["opening_hours"] = OpeningHours()
            for day_hours in location["openingHours"]["weekDayOpeningList"]:
                if day_hours["closed"]:
                    continue
                item["opening_hours"].add_range(
                    day_hours["weekDay"],
                    day_hours["openingTime"]["formattedHour"],
                    day_hours["closingTime"]["formattedHour"],
                    "%I:%M %p",
                )

            yield item
