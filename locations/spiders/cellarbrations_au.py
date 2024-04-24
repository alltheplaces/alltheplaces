from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class CellarbrationsAUSpider(Spider):
    name = "cellarbrations_au"
    item_attributes = {"brand": "Cellarbrations", "brand_wikidata": "Q109807592"}
    allowed_domains = ["storefrontgateway.cellarbrations.com.au"]
    start_urls = [
        "https://storefrontgateway.cellarbrations.com.au/api/near/-33.867778/151.21/20000/20000/stores",
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["items"]:
            if location.get("status") != "Active":
                continue
            item = DictParser.parse(location)
            item["ref"] = location["retailerStoreId"]
            item["name"] = item["name"].strip()
            item["city"] = item["city"].strip()
            item["street_address"] = ", ".join(
                filter(None, [location.get("addressLine1"), location.get("addressLine2"), location.get("addressLine3")])
            ).strip()
            item["state"] = location.get("countyProvinceState")
            if location.get("openingHours"):
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_ranges_from_string(location["openingHours"])
            yield item
