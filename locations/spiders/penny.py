from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.spiders.penny_de import PennyDESpider


class PennySpider(Spider):
    name = "penny"
    item_attributes = PennyDESpider.item_attributes

    def start_requests(self):
        for country in ["at", "cz", "hu", "it", "ro"]:
            yield JsonRequest(url=f"https://www.penny.{country}/api/stores", cb_kwargs={"cc": country})

    def parse(self, response, **kwargs):
        for store in response.json():
            store["lat"] = store["position"]["lat"]
            store["lon"] = store["position"]["lng"]
            store["street_address"] = store.pop("street")
            store["country"] = kwargs["cc"].upper()

            yield DictParser.parse(store)
