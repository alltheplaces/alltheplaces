import scrapy
import json
from locations.dict_parser import DictParser


class McCollsGBSpider(scrapy.Spider):
    name = "mccolls_gb"
    item_attributes = {
        "brand": "McColl's",
        "brand_wikidata": "Q16997477",
    }
    start_urls = ["https://www.mccolls.co.uk/storelocator/"]
    download_delay = 0.5

    def parse(self, response):
        script = json.loads(
            response.xpath('//script[contains(., "allStores")]/text()').get()
        )
        for store in DictParser.get_nested_key(script, "items"):
            yield scrapy.Request(
                store["store_url"],
                self.parse_store,
                cb_kwargs=dict(store=store),
            )

    def parse_store(self, response, store):
        item = DictParser.parse(store)
        item["website"] = response.url
        item["street_address"] = store.get("address")
        # TODO: open hours available in both store JSON and page response
        return item
