import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import city_locations


class SuzukiDESpider(scrapy.Spider):
    name = "suzuki_de"
    item_attributes = {"brand": "Suzuki", "brand_wikidata": "Q181642"}

    def start_requests(self):
        yield from self.request_for_data()

    def request_for_data(self):
        for city in city_locations("DE", 50000):
            form_data = {
                "dealertype": ["V", "S"],
                "searchtype": "2",
                "count": "20",
                "radius": "50",
                "lat": str(city["latitude"]),
                "lng": str(city["longitude"]),
            }

            yield scrapy.http.FormRequest(
                url="https://auto.suzuki.de/dealersearch/search",
                formdata=form_data,
            )

    def parse(self, response):
        for store in response.json():
            store["location"]["name"] = store["dealer"].get("dealername")
            store["location"]["website"] = store["dealer"].get("homepage")
            store["location"]["province"] = store["dealer"].get("province")
            item = DictParser.parse(store["location"])
            apply_category(Categories.SHOP_CAR, item)
            yield item
