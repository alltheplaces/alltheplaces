from scrapy import Spider

from locations.categories import Categories
from locations.dict_parser import DictParser


class RottenRobbieUSSpider(Spider):
    name = "rotten_robbie_us"
    item_attributes = {"brand": "Rotten Robbie", "brand_wikidata": "Q87378070", "extras": Categories.FUEL_STATION.value}
    start_urls = [
        "https://www.rottenrobbie.com/wp-json/wpgmza/v1/features/base64eJyrVkrLzClJLVKyUqqOUcpNLIjPTIlRsopRMoxRqlWqBQCnUQoG"
    ]

    def parse(self, response, **kwargs):
        yield from map(DictParser.parse, response.json()["markers"])
