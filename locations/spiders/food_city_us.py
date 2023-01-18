import html

from scrapy import Spider

from locations.dict_parser import DictParser


class FoodCityUSSpider(Spider):
    name = "food_city_us"
    item_attributes = {"brand": "Food City", "brand_wikidata": "Q16981107"}
    start_urls = ["https://myfoodcity.com/wp-admin/admin-ajax.php?action=store_search&max_results=250&autoload=1"]

    def parse(self, response, **kwargs):
        for location in response.json():
            location["name"] = html.unescape(location.pop("store"))
            location["street_address"] = ", ".join(filter(None, [location.pop("address"), location.pop("address2")]))

            yield DictParser.parse(location)
