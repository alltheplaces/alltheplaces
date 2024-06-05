from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address
from locations.user_agents import FIREFOX_LATEST


class TiffanySpider(Spider):
    name = "tiffany"
    item_attributes = {"brand": "Tiffany", "brand_wikidata": "Q1066858"}
    allowed_domains = ["www.tiffany.com"]
    start_urls = ["https://www.tiffany.com/content/tiffany-n-co/_jcr_content/servlets/storeslist.1.json"]
    user_agent = FIREFOX_LATEST  # ATP and older user agents are blocked.
    requires_proxy = True  # Data centre netblocks appear to be blocked.

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["resultDto"]:
            item = DictParser.parse(location["store"])
            if "TEMPORARILY CLOSED" in item["name"].upper():
                continue
            item["lat"] = location["store"]["geoCodeLattitude"]
            item["lon"] = location["store"]["geoCodeLongitude"]
            item["street_address"] = clean_address(
                [
                    location["store"].get("address1"),
                    location["store"].get("address2"),
                    location["store"].get("address3"),
                ]
            )
            item["phone"] = location["store"]["phone"].split("/", 1)[0].strip()
            item["website"] = (
                "https://www.tiffany.com/jewelry-stores/" + location["storeSeoAttributes"][0]["canonicalUrlkeyword"]
            )
            if location["store"]["storePhoto"] != "/shared/images/stores/store_location.jpg":
                item["image"] = "https://www.tiffany.com" + location["store"]["storePhoto"]
            opening_soon = False
            for store_hours in location["storeHours"]:
                if store_hours.get("storeHourTypeId", 0) == 1:
                    if "OPENING SOON" in store_hours["storeHours"].upper():
                        opening_soon = True
                        break
                    item["opening_hours"] = OpeningHours()
                    item["opening_hours"].add_ranges_from_string(
                        store_hours["storeHours"].replace("<br>", "").replace(".", "")
                    )
            if opening_soon:
                continue
            yield item
