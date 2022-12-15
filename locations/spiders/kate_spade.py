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
        for ref, store in response.json()["stores"].items():
            item = DictParser.parse(store)
            item["lat"] = store.get("latitude").replace(",", ".")
            item["lon"] = store.get("longitude").replace(",", ".")
            item["ref"] = ref
            item["website"] = f'https://{self.allowed_domains[0]}{store.get("storeURL")}'

            yield item
