import scrapy

from locations.items import Feature


class KroshkaKartoshkaRUSpider(scrapy.Spider):
    name = "kroshka_kartoshka_ru"
    item_attributes = {"brand_wikidata": "Q4241838"}
    start_urls = ["https://www.kartoshka.com/ajax/shops/"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response, **kwargs):
        for shop in response.json()["features"]:
            item = Feature()
            item["ref"] = shop["id"]
            item["geometry"] = shop["geometry"]
            item["name"] = shop["properties"]["balloonTitle"]
            item["street_address"] = shop["properties"]["balloonAddress"]
            item["phone"] = shop["properties"]["balloonPhone"]
            yield item
