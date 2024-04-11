import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import city_locations


class StarbucksKZSpider(scrapy.Spider):
    name = "starbucks_kz"
    item_attributes = {"brand": "Starbucks", "brand_wikidata": "Q37158"}

    def start_requests(self):
        for city in city_locations("KZ", 100000):
            url = f"https://www.starbucks.com.kz/api/v1/store-finder?latLng={city['latitude']}%2C{city['longitude']}"
            yield JsonRequest(url=url)

    def parse(self, response, **kwargs):
        for store in response.json()["stores"]:
            item = DictParser.parse(store)
            item["website"] = "https://starbucks.com.kz/"
            apply_category(Categories.CAFE, item)
            yield item
