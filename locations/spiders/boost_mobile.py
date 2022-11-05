import json

import scrapy

from locations.dict_parser import DictParser
from locations.geo import postal_regions


class BoostMobileSpider(scrapy.Spider):
    name = "boost_mobile"
    item_attributes = {
        "brand": "Boost Mobile",
        "brand_wikidata": "Q4943790",
        "country": "US",
    }
    download_delay = 0.2

    def start_requests(self):
        for record in postal_regions("US"):
            template_url = "https://boostmobile.nearestoutlet.com/cgi-bin/jsonsearch-cs.pl?showCaseInd=false&brandId=bst&results=50&zipcode={}"
            yield scrapy.Request(template_url.format(record["postal_region"]))

    def parse(self, response):
        data = json.loads(json.dumps(response.json()))
        stores = DictParser.get_nested_key(data, "nearestLocationInfo")
        if not stores:
            return
        for store in stores:
            if store["storeName"].startswith("Boost Mobile"):
                item = DictParser.parse(store["storeAddress"])
                item["ref"] = store["id"]
                item["name"] = store["storeName"]
                item["street_address"] = store["storeAddress"]["primaryAddressLine"]
                yield item
