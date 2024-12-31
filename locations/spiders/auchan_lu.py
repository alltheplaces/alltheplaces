import scrapy
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser


class AuchanLUSpider(scrapy.Spider):
    name = "auchan_lu"
    item_attributes = {"brand": "Auchan", "brand_wikidata": "Q758603"}

    def start_requests(self):
        yield JsonRequest(
            url="https://api.ari.auchan.com/ari/digit/portal-cms/lu/template/stores?context=push-stores-list",
            headers={"X-Gravitee-Api-Key": "226ec165-1e26-45c8-a5ed-25a2cd3c5329"},
        )

    def parse(self, response, **kwargs):
        for store in response.json():
            store.update(store.pop("address"))
            item = DictParser.parse(store)
            item["website"] = "https://www.auchan.lu/fr/retail/" + store["pageName"]
            yield item
