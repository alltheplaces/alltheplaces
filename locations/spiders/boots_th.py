from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import Request

from locations.dict_parser import DictParser


class BootsTHSpider(Spider):
    name = "boots_th"
    item_attributes = {"brand": "Boots", "brand_wikidata": "Q6123139"}

    async def start(self) -> AsyncIterator[Request]:
        yield self.get_page(1)

    def get_page(self, n: int) -> Request:
        return Request(
            f"https://store.boots.co.th/api/v1/branches/web?locale=en&latitude=0&longitude=0&filter_type=1&page={n}",
            meta={"page": n},
        )

    def parse(self, response):
        data = response.json()
        stores = data["entities"]

        for store in stores:
            item = DictParser.parse(store)
            item["ref"] = store["store_code"]
            item["phone"] = store["phone_list"][0]
            item["postcode"] = store["zipcode"]
            yield item

        if data["page_information"]["page"] < data["page_information"]["number_of_page"]:
            yield self.get_page(1 + response.meta["page"])
