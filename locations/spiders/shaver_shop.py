import re

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class ShaverShopSpider(Spider):
    name = "shaver_shop"
    item_attributes = {"brand": "Shaver Shop", "brand_wikidata": "Q119443589"}
    allowed_domains = ["www.shavershop.com.au", "www.shavershop.net.nz"]
    start_urls = [
        "https://www.shavershop.com.au/on/demandware.store/Sites-Shaver_Shop_au-Site/en_AU/Stores-GetAllStores?countryCode=AU",
        "https://www.shavershop.net.nz/on/demandware.store/Sites-Shaver_Shop_nz-Site/en_NZ/Stores-GetAllStores?countryCode=NZ",
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["stores"]:
            item = DictParser.parse(location)
            if "shavershop.net.nz" in response.url:
                item["website"] = (
                    "https://www.shavershop.net.nz/stores/"
                    + location["stateCode"]
                    + "/"
                    + location["city"]
                    + "/"
                    + location["id"]
                )
                item.pop("state")
            else:
                item["website"] = "https://www.shavershop.com.au/stores/" + location["stateCode"] + "/" + location["id"]
            hours_string = re.sub(r"\s+", " ", location["storeHours"].replace("<br />", "").replace("<p>", "")).strip()
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)
            yield item
