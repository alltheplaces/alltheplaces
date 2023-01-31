from scrapy import Spider

from locations.dict_parser import DictParser


class ArcticCircleUSSpider(Spider):
    name = "arctic_circle_us"
    item_attributes = {"brand": "Arctic Circle", "brand_wikidata": "Q4787501"}
    start_urls = ["https://media.acburger.com/api/locations/json"]

    def parse(self, response, **kwargs):
        for store in response.json():
            if store["published"] != "1":
                continue

            store["ref"] = store.pop("store")
            store["street_address"] = store.pop("address")

            yield DictParser.parse(store)
