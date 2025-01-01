import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class PizzaHutSGSpider(scrapy.Spider):
    name = "pizza_hut_sg"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    start_urls = [
        "https://1war1y0px0.execute-api.ap-southeast-1.amazonaws.com/Prod/api/address/GetAvailableStores?latitude=1.385486&longitude=103.845825&radiusKilometers=50"
    ]

    def parse(self, response):
        for poi in response.json()["result"]:
            poi.update(poi.pop("collectionPointGeoLocation"))
            item = DictParser.parse(poi)
            item["ref"] = poi.get("autoId")
            item["street_address"] = poi.get("collectionPointAddress1")
            item["postcode"] = poi.get("collectionPointPostalCode")
            apply_category(Categories.RESTAURANT, item)

            yield item
