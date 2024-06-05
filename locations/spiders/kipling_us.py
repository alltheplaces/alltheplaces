import re

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class KiplingUSSpider(Spider):
    name = "kipling_us"
    item_attributes = {"brand": "Kipling", "brand_wikidata": "Q6414641"}
    allowed_domains = ["www.kipling-usa.com"]
    start_urls = [
        "https://www.kipling-usa.com/on/demandware.store/Sites-kip-Site/default/Stores-GetNearestStores?&countryCode=US&onlyCountry=true&retailstores=true&outletstores=true"
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json().values():
            if (
                "STORE CLOSED" in location.get("storeHours", "").upper()
                or "STORE IS CLOSED" in location.get("storeHours", "").upper()
            ):
                continue
            item = DictParser.parse(location)
            item["ref"] = location["storeID"]
            item["street_address"] = clean_address([location.get("address1"), location.get("address2")])
            hours_string = re.sub(r"\s+", " ", location.get("storeHours")).strip()
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)
            yield item
