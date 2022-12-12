import scrapy

from locations.dict_parser import DictParser
from locations.geo import postal_regions


class SparGBSpider(scrapy.Spider):
    name = "spar_gb"
    item_attributes = {"brand": "SPAR", "brand_wikidata": "Q610492"}
    custom_settings = {"ROBOTSTXT_OBEY": False}
    download_delay = 1.0

    def start_requests(self):
        for record in postal_regions("GB"):
            yield scrapy.Request(
                "https://www.spar.co.uk/umbraco/api/storelocationapi/stores?location={}".format(record["postal_region"])
            )

    def parse(self, response):
        for store in response.json()["storeList"]:
            item = DictParser.parse(store)
            item["website"] = "https://www.spar.co.uk" + store["StoreUrl"]
            item["street_address"] = store.get("Address1")
            yield item
