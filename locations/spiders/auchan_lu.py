import scrapy
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser

AUCHAN_DRIVE = {"brand": "Auchan Drive", "brand_wikidata": "Q2870659"}
MY_AUCHAN = {"brand": "My Auchan", "brand_wikidata": "Q115800307"}
AUCHAN = {"brand": "Auchan", "brand_wikidata": "Q758603"}


class AuchanLUSpider(scrapy.Spider):
    name = "auchan_lu"

    def start_requests(self):
        yield JsonRequest(
            url="https://api.ari.auchan.com/ari/digit/portal-cms/lu/template/stores?context=push-stores-list",
            headers={"X-Gravitee-Api-Key": "226ec165-1e26-45c8-a5ed-25a2cd3c5329"},
        )

    def parse(self, response, **kwargs):
        for store in response.json():
            store.update(store.pop("address"))
            item = DictParser.parse(store)

            item["website"] = item["extras"]["website:fr"] = "https://www.auchan.lu/fr/retail/{}".format(
                store["pageName"]
            )
            item["extras"]["website:en"] = "https://www.auchan.lu/en/retail/{}".format(store["pageName"])
            item["extras"]["website:de"] = "https://www.auchan.lu/de/retail/{}".format(store["pageName"])

            if store["type"] == "1":
                item.update(AUCHAN_DRIVE)
                item["branch"] = item.pop("name").removeprefix("Auchan Drive ")
            elif store["type"] in ["3", "4"]:
                item.update(AUCHAN)
                item["branch"] = item.pop("name").removeprefix("Auchan ")
            elif store["type"] == "5":
                item.update(MY_AUCHAN)
                item["branch"] = item.pop("name").removeprefix("MyAuchan ").removeprefix("My Auchan ")

            yield item
