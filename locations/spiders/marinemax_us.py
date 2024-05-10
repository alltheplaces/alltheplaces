from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import clean_address


class MarineMaxUSSpider(Spider):
    name = "marinemax_us"
    item_attributes = {"brand": "MarineMax", "brand_wikidata": "Q119140995"}
    allowed_domains = ["mes124x9ka-1.algolianet.com"]
    start_urls = [
        "https://mes124x9ka-1.algolianet.com/1/indexes/StoreLocations/?x-algolia-application-id=MES124X9KA&x-algolia-api-key=2a57d01f2b35f0f1c60cb188c65cab0d&hitsPerPage=1000"
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["hits"]:
            if not location["isActive"]:
                continue
            item = DictParser.parse(location)
            item["ref"] = location["IDS_Site_ID"]
            item["lat"] = location["_geoloc"]["lat"]
            item["lon"] = location["_geoloc"]["lng"]
            item["street_address"] = clean_address([location["Address1"], location["Address2"]])
            item["state"] = location["State"]
            item["email"] = location["OwnerEmailAddress"]
            item["website"] = location["LocationPageURL"]
            yield item
