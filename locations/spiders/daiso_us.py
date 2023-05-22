from scrapy import Spider

from locations.dict_parser import DictParser


class DaisoUSSpider(Spider):
    name = "daiso_us"
    item_attributes = {"brand": "Daiso Japan", "brand_wikidata": "Q866991"}
    start_urls = ["https://cdn.shopify.com/s/files/1/0431/1842/8321/t/59/assets/sca.storelocatordata.json"]

    def parse(self, response, **kwargs):
        for location in response.json():
            location["street_address"] = location.pop("address")
            yield DictParser.parse(location)
