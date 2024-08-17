from scrapy import Spider

from locations.dict_parser import DictParser


class HaysTravelGBSpider(Spider):
    name = "hays_travel_gb"
    item_attributes = {"brand": "Hays Travel", "brand_wikidata": "Q70250954"}
    start_urls = ["https://branches.haystravel.co.uk/api/branches"]

    def parse(self, response):
        for store in response.json()["data"]:
            yield DictParser.parse(store)
