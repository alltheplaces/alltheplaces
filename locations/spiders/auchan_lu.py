import scrapy
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser


class AuchanLUSpider(scrapy.Spider):
    name = "auchan_lu"
    item_attributes = {"brand": "Auchan", "brand_wikidata": "Q758603"}

    def start_requests(self):
        yield JsonRequest(
            url="https://api.auchan.com/corp/cms/v4/lu/template/stores",
            headers={"X-Gravitee-Api-Key": "f303247f-d0d9-4036-9232-6b9cca51ca6d"},
        )

    def parse(self, response, **kwargs):
        for store in response.json():
            store.update(store.pop("address"))
            item = DictParser.parse(store)
            yield item
