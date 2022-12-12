import scrapy

from locations.dict_parser import DictParser


class NordstromSpider(scrapy.Spider):
    name = "nordstrom"
    item_attributes = {"brand": "Nordstrom", "brand_wikidata": "Q174310"}
    allowed_domains = ["api.nordstrom.com"]
    start_urls = [
        "https://api.nordstrom.com/v2/store/locator?apikey=Gneq2B6KqSbEABkg9IDRxuxAef9BqusJ&apigee_bypass_cache=1&format=json",
    ]

    def parse_store(self, response):
        for store in response.json()["stores"]:
            if store.get("type") == "Rack":
                # Also in the nordstrom_rack spider
                continue

            item = DictParser.parse(store)

            item["ref"] = store.get("number")

            item["street_address"] = store.get("address")
            item["addr_full"] = None

            item["website"] = "https://www.nordstrom.com/store-details/" + store.get("path")

            item["extras"] = {}
            item["extras"]["type"] = store.get("type")

            yield item

    def parse(self, response):
        ids = []
        for _, state in response.json().items():
            for _, city in state.items():
                for id in city:
                    ids.append(id)

        yield scrapy.Request(
            "https://api.nordstrom.com/v2/store/list?apikey=Gneq2B6KqSbEABkg9IDRxuxAef9BqusJ&apigee_bypass_cache=1&format=json&storeNumbers="
            + ",".join(ids),
            callback=self.parse_store,
        )
