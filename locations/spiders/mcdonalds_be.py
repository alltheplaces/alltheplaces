import scrapy
from locations.dict_parser import DictParser
from locations.spiders.mcdonalds import McDonaldsSpider


class McDonaldsBESpider(scrapy.Spider):
    name = "mcdonalds_be"
    item_attributes = McDonaldsSpider.item_attributes
    start_urls = ["https://mcdonalds.be/en/restaurants/api/restaurants"]

    def parse(self, response):
        def fix(s):
            return float(s) / 1000000.0

        for store in response.json():
            item = DictParser.parse(store)
            item["website"] = "https://www.mcdonalds.be/en/restaurants/" + store["slug"]
            item["street_address"] = store.get("street_en")
            item["city"] = store.get("city_en")
            item["lat"] = fix(store["lat_times_a_million"])
            item["lon"] = fix(store["lng_times_a_million"])
            yield item
