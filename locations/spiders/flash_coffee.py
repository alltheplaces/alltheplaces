from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_yes_no, Extras
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class FlashCoffeeSpider(Spider):
    name = "flash_coffee"
    item_attributes = {
        "brand": "Flash Coffee",
        "brand_wikidata": "Q118627777",
        "extras": Categories.CAFE.value,
    }
    start_urls = ["https://content-gateway.flash-coffee.com/api/stores?contentType=storesId"]

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)

            apply_yes_no(Extras.OUTDOOR_SEATING, item, location["outdoorSeating"])
            # "indoorSeating": true,
            # "outdoorSeating": false,
            # "music": true,
            # "glassdoor": true,
            # "tv": true,
            # "ambientDisplay": true,
            # "chillerDisplay": true,
            # "iceBin": false,
            # "iceMachine": false,
            # "manualPlumbing": false,
            # "staffToilet": false,
            # "customerToilet": false,
            apply_yes_no(Extras.TOILETS, item, location["customerToilet"])
            # "centralKitchen": false,
            # "topview": false
            yield item
