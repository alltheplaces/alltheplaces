import scrapy

from locations.dict_parser import DictParser


class KateSpadeSpider(scrapy.Spider):
    name = "kate_spade"
    item_attributes = {
        "brand": "KateSpade",
        "brand_wikidata": "Q275094",
    }
    allowed_domains = ["eu.katespade.com"]
    start_urls = [
        "https://eu.katespade.com/on/demandware.store/Sites-ksEuRoe-Site/en_FR/Stores-GetNearestStores?latitude=39.629490&longitude=-100.059825&distanceUnit=Meilen&maxdistance=300000"
    ]

    def parse(self, response):
        stores = response.json().get("stores")
        for store_id in stores:
            item = DictParser.parse(stores.get(store_id))
            item["lat"] = stores.get(store_id, {}).get("latitude").replace(",", ".")
            item["lon"] = stores.get(store_id, {}).get("longitude").replace(",", ".")
            item["ref"] = stores.get(store_id, {}).get("name")
            item["website"] = f'{self.allowed_domains[0]}{stores.get(store_id, {}).get("storeURL")}'

            yield item
