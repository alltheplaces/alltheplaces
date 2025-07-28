import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class SportclubARSpider(scrapy.Spider):
    name = "sportclub_ar"
    item_attributes = {"brand": "SportClub", "brand_wikidata": "Q118314171"}
    custom_settings = {
        "DOWNLOAD_TIMEOUT": 120,
    }

    def start_requests(self):
        yield JsonRequest(
            url="https://vhzfd7sis7qzlcy63dcjgc2cqa0lovrs.lambda-url.sa-east-1.on.aws/v1/sedes?limit=1000",
            headers={
                "api-key": "SECRET_KEY",
            },
        )

    def parse(self, response, **kwargs):
        for club in response.json()["response"]["results"]:
            item = DictParser.parse(club)
            item["geometry"] = club["location"]
            item["geometry"]["type"] = "Point"
            item["street_address"] = club.get("direccion")
            item["city"] = club.get("zona")
            item["state"] = club.get("provincia")
            item["phone"] = club.get("telefono")
            item["website"] = "https://www.sportclub.com.ar/sedes/" + club.get("slug", "")
            apply_category(Categories.GYM, item)
            yield item
