import scrapy

from locations.dict_parser import DictParser


# This spider has a potential to be a Sitemap/StructuredData Spider once we start proxying requests.
class ColruytSpider(scrapy.Spider):
    name = "colruyt"
    item_attributes = {"brand": "Colruyt", "brand_wikidata": "Q2363991"}
    start_urls = [
        "https://ecgplacesmw.colruyt.be/ecgplacesmw/v3/nl/places/searchPlaces?ensignId=8&placeTypeId=1"
    ]

    def parse(self, response):
        for store in response.json():
            store["address"]["city"] = store["address"].pop("cityName")
            store["address"]["country"] = store["address"].pop("countryName")
            store["location"] = store.pop("geoCoordinates")
            store["website"] = store["moreInfoUrl"]
            store["ref"] = store["placeId"]
            yield DictParser.parse(store)
