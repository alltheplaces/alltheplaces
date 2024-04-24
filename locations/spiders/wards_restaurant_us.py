import html

from scrapy import Spider

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class WardsRestaurantUSSpider(Spider):
    name = "wards_restaurant_us"
    item_attributes = {"brand": "Ward's Restaurant", "brand_wikidata": "Q119716752"}
    start_urls = ["https://wardsrestaurants.com/?sm-xml-search=1"]

    def parse(self, response, **kwargs):
        for location in response.json():
            location["street_address"] = merge_address_lines([location.pop("address"), location.pop("address2")])
            location["name"] = html.unescape(location["name"])
            yield DictParser.parse(location)
