import json

from scrapy import Spider
from scrapy.http import Response

from locations.categories import apply_yes_no
from locations.dict_parser import DictParser


class AdidasSpider(Spider):
    name = "adidas"
    item_attributes = {"brand": "Adidas", "brand_wikidata": "Q3895"}
    start_urls = [
        "https://placesws.adidas-group.com/API/search?brand=adidas&geoengine=google&method=get&category=store&format=json&storetype=ownretail&latlng=0%2C0"
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs):
        data = json.loads(response.body.replace(b"\n", b"\\n").replace(b"\r", b"\\r").replace(b"\\2", b"\\\\2"))
        for shop in data["wsResponse"]["result"]:
            item = DictParser.parse(shop)
            item["lat"] = shop["latitude_google"]
            item["lon"] = shop["longitude_google"]
            item["street_address"] = shop["street1"]
            item["email"] = shop.get("email1")
            slug = (
                "-".join([shop["city"], shop["street1"], shop["name"]])
                .lower()
                .replace(" ", "-")
                .replace(",", "")
                .replace("/", "")
            )
            item["website"] = f"https://www.adidas.co.uk/storefront/{item['ref']}-{slug}"
            apply_yes_no("factory_outlet", item, shop.get("factory_outlet") == "1")
            yield item
