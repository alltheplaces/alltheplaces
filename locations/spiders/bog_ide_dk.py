import scrapy

from locations.dict_parser import DictParser


class BogIdeDKSpider(scrapy.Spider):
    name = "bog_ide_dk"
    item_attributes = {"brand": "Bog & idé", "brand_wikidata": "Q12303981"}
    start_urls = ["https://api.bog-ide.dk/scom/api/stores/get?lat=0&lng=0&limit=500"]

    def parse(self, response):
        for store in response.json():
            store.update(store.pop("Address"))
            store["street_address"] = store.pop("StreetAndNumber")
            item = DictParser.parse(store)
            item["name"] = store["CustomerName"]
            item["website"] = "https://www.bog-ide.dk/boghandler/" + store["CustomerWebName"]
            yield item
