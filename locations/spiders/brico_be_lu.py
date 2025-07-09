import scrapy

from locations.dict_parser import DictParser


class BricoBELUSpider(scrapy.Spider):
    name = "brico_be_lu"
    item_attributes = {"brand": "Brico", "brand_wikidata": "Q2510786"}
    start_urls = ["https://www.brico.be/nl/store-finder"]

    def parse(self, response):
        for store_url in response.xpath('//a[contains(@href, "/storedetail/")]/@href').getall():
            id = store_url.split("/")[2]
            yield scrapy.Request(
                url="https://www.brico.be/rest/v1/storefinder/store/{}?format=brico&lang=nl_BE".format(id),
                callback=self.parse_store,
                cb_kwargs=dict(website=store_url),
            )

    def parse_store(self, response, website):
        store = response.json()
        store.update(store.pop("address"))
        item = DictParser.parse(store)
        item["ref"] = item.pop("name")
        item["website"] = "https://www.brico.be/nl" + website
        yield item
