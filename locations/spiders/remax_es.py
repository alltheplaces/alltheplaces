from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser


class RemaxESSpider(Spider):
    name = "remax_es"
    item_attributes = {
        "brand": "RE/MAX",
        "brand_wikidata": "Q965845",
    }
    allowed_domains = ["www.remax.es"]
    start_urls = ["https://www.remax.es/buscador-de-oficinas/jsonData.php"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url, headers={"X-Requested-With": "XMLHttpRequest"})

    def parse(self, response):
        for location in response.json().values():
            item = DictParser.parse(location)
            item["ref"] = location["id_oficina_anaconda"]
            item["name"] = location["headline"]
            item["lat"] = location["la"]
            item["lon"] = location["lo"]
            item["website"] = location["post_name"].replace("mls.remax.es", "www.remax.es")
            yield item
