from typing import Any, AsyncIterator

import scrapy
from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import country_iseadgg_centroids
from locations.items import Feature


class IpirangaBRSpider(Spider):
    name = "ipiranga_br"
    item_attributes = {"brand": "Ipiranga", "brand_wikidata": "Q2081136"}
    start_urls = ["https://localizador.ipiranga.com.br/"]

    def parse(self, response: Any) -> AsyncIterator[Any]:
        token = response.xpath('//*[@name="token-acesso"]/@content').get()
        yield scrapy.Request(
            "https://localizador.ipiranga.com.br/find-posto?promo=&tipo=todos&filtroDistancia=500000000&posLat=-22.906927126561026&posLong=-43.22561847094725",
            headers={
                "Referer": "https://localizador.ipiranga.com.br/",
                "x-token-acesso": f"{token}",
            },
            callback=self.parse_store_id,
        )

    def parse_store_id(self, response: Any) -> AsyncIterator[Any]:
        for location in response.json():
            item = DictParser.parse(location)
            yield scrapy.Request(
                url=f"https://localizador.ipiranga.com.br/find-place?id={item['ref']}",
                meta={"item": item},
                callback=self.parse_details,
            )

    def parse_details(self, response):
        item = response.meta["item"]
        item["addr_full"] = response.xpath('//*[@class="card-body_info"]/p[2]/text()').get()
        item["website"] = response.url
        item["branch"] = item.pop("name")
        item["name"] = self.item_attributes["brand"]
        apply_category(Categories.FUEL_STATION, item)
        yield item
