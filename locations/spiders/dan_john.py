from scrapy import Spider

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import clean_address


class DanJohnSpider(Spider):
    name = "dan_john"
    item_attributes = {"brand": "Dan John", "brand_wikidata": "Q116304215"}
    start_urls = ["https://stores.danjohn.com/js_db/stores-json-en.json"]

    def parse(self, response, **kwargs):
        for location in response.json():
            if location["storeTypeLabels"] != ["DANJOHN"]:
                continue
            location["street_address"] = clean_address([location.pop("address1"), location.pop("address2")])
            location["country"] = location["country"]["tagISO31661Alpha2"]
            item = DictParser.parse(location)
            item["image"] = ";".join(location["miniPhotos"])

            yield item
