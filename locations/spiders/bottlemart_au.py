from scrapy import Spider

from locations.dict_parser import DictParser


class BottlemartAUSpider(Spider):
    name = "bottlemart_au"
    item_attributes = {"brand": "Bottlemart", "brand_wikidata": "Q102863175"}
    start_urls = [
        "https://app.ehoundplatform.com/api/1.4/proximity_search?output=json&lat=-31.95224&lon=115.8614&count=10000&api_key=1qt7ts2bsw8a73v"
    ]

    def parse(self, response, **kwargs):
        for location in response.json()["record_set"]:
            item = DictParser.parse(location)
            item["ref"] = location["loc_id"]
            item["name"] = location["details"]["location_name"]
            item["phone"] = location["details"]["phone"]

            yield item
