import scrapy

from locations.dict_parser import DictParser


class TeknikmagasinetSESpider(scrapy.Spider):
    name = "teknikmagasinet_se"
    start_urls = [
        "https://www.teknikmagasinet.se/_next/data/l27oTv8kIMOzrHw2WFLQi/sv/teknikmagasinet/find-your-store.json"
    ]
    item_attributes = {"brand": "Teknikmagasinet", "brand_wikidata": "Q3357520"}

    def parse(self, response, **kwargs):
        d = response.json().get("pageProps").get("data").get("shops")
        for store in d:
            store["street_address"] = store.pop("Address")
            yield DictParser.parse(store)
