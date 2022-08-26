import scrapy
from locations.dict_parser import DictParser


class CarrefourSpider(scrapy.Spider):
    name = "carrefour_ar"
    item_attributes = {"brand": "Carrefour", "brand_wikidata": "Q217599"}
    # TODO: I suspect other Carrefour domains have this very same interface
    start_urls = [
        "https://www.carrefour.com.ar/_v/public/graphql/v1?workspace=master&maxAge=short&appsEtag=remove&domain=store&locale=es-AR&operationName=getStoreLocations&variables=%7B%7D&extensions=%7B%22persistedQuery%22%3A%7B%22version%22%3A1%2C%22sha256Hash%22%3A%22a84a4ca92ba8036fe76fd9e12c2809129881268d3a53a753212b6387a4297537%22%2C%22sender%22%3A%22lyracons.lyr-store-locator%400.x%22%2C%22provider%22%3A%22vtex.store-graphql%402.x%22%7D%2C%22variables%22%3A%22eyJhY2NvdW50IjoiY2FycmVmb3VyYXIifQ%3D%3D%22%7D"
    ]

    def parse(self, response):
        for data in response.json()["data"]["documents"]:
            o = {}
            for field in data["fields"]:
                value = field.get("value", "null")
                if not value == "null":
                    o[field["key"]] = value
            o["name"] = o.get("businessName")
            o["phone"] = o.get("primaryPhone")
            o["city"] = o.get("locality")
            o["state"] = o.get("administrativeArea")
            # TODO: opening hours are available
            yield DictParser.parse(o)
