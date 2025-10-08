import scrapy

from locations.dict_parser import DictParser


class ScapinoNLSpider(scrapy.Spider):
    name = "scapino_nl"
    item_attributes = {"brand": "Scapino", "brand_wikidata": "Q2298792"}
    start_urls = ["https://www.scapino.nl/winkels/index.pageContext.json"]

    def parse(self, response):
        for store in response.json()["pageProps"]["stores"]:
            item = DictParser.parse(store)
            yield item
