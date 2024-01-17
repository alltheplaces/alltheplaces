import scrapy

from locations.dict_parser import DictParser


class FastracCafeUSSpider(scrapy.Spider):
    name = "fastrac_cafe_us"
    item_attributes = {"brand": "Fastrac Cafe", "brand_wikidata": "Q117324848"}
    # A pageNumber higher than available gives us all the POIs
    start_urls = ["https://fastraccafe.com/api/stores-locator/store-locator-search/results?bannerId=16&pageNumber=100"]

    def parse(self, response, **kwargs):
        for location in response.json()["value"]["mapResults"]:
            location["street_address"] = location.pop("address")
            location["url"] = location.pop("pageUrl")

            yield DictParser.parse(location)
