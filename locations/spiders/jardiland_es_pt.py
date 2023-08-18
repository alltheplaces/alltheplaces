from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.spiders.jardiland_fr import JardilandFRSpider


class JardilandESPTSpider(Spider):
    name = "jardiland_es_pt"
    item_attributes = JardilandFRSpider.item_attributes
    allowed_domains = ["www.jardiland.es"]
    start_urls = ["https://www.jardiland.es/tiendas/getList/"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["listado"]:
            item = DictParser.parse(location)
            if "Portugal" in item["state"] or "Portugal" in item["addr_full"]:
                item["country"] = "PT"
                item["state"] = item["state"].replace("(Portugal)", "").strip()
                item["addr_full"] = item["addr_full"].replace("(Portugal)", "").strip()
            else:
                item["country"] = "ES"
            yield item
