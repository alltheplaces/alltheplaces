import scrapy

from locations.dict_parser import DictParser


class PopeyesAESpider(scrapy.Spider):
    name = "popeyes_ae"
    item_attributes = {"brand": "Popeyes", "brand_wikidata": "Q1330910"}
    start_urls = ["https://pe-uae-ordering-api-fd-cadfduawfaavf2bz.z01.azurefd.net/api/v2/restaurants"]

    def parse(self, response, **kwargs):
        for store in response.json()["data"]:
            store.update(store["storeLocation"].pop("coordinates"))
            item = DictParser.parse(store)
            item["addr_full"] = store.get("storeAddress")
            item["website"] = "https://www.popeyesuae.com/locations/" + item["name"].replace(" ", "-")
            yield item
