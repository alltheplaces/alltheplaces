import json
from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import Request

from locations.items import Feature


class EcopackBGSpider(Spider):
    name = "ecopack_bg"
    item_attributes = {"operator": "Екопак", "operator_wikidata": "Q116687081", "country": "BG"}
    allowed_domains = ["ecopack.bg"]
    start_urls = ["https://www.ecopack.bg/bg/containers_xhr/?method=pins"]
    no_refs = True

    async def start(self) -> AsyncIterator[Request]:
        headers = {
            "X-Requested-With": "XMLHttpRequest",
        }
        for url in self.start_urls:
            yield Request(url, headers=headers)

    def parse(self, response):
        data = json.loads(response.text)
        for municipality in data.get("municipalities"):
            for city in municipality.get("locations"):
                for container in city.get("items", []):
                    item = Feature()
                    item["city"] = city.get("title").replace("гр.", "").replace("с.", "").strip()
                    item["street_address"] = container.get("formatted_address")
                    item["lat"] = container.get("lat")
                    item["lon"] = container.get("lon")

                    yield item
