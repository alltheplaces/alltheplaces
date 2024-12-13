import re
from typing import Iterable

import scrapy
from lxml import etree
from scrapy import http

from locations.categories import Categories, apply_category
from locations.pipelines.address_clean_up import clean_address

MAP_SCRIPT_REGEX = re.compile(r"google\.maps\.LatLng\([ ]*([-0-9.]*)[ ]*,[ ]*([-0-9.]*)[ ]*\);")


class EspressolabSpider(scrapy.Spider):
    name = "espressolab"
    item_attributes = {"brand": "Espressolab", "brand_wikidata": "Q97599059"}

    def start_requests(self) -> Iterable[scrapy.Request]:
        yield scrapy.Request(url="https://espressolab.com/subeler/", callback=self.parse_stores_page)

    def parse_stores_page(self, response: http.HtmlResponse):
        for url_path in response.xpath("/html/body/form/div[4]/div[4]/div[1]/div/div/div/div[1]/div/div/div[2]/ul/li/a/@href").getall():
            yield scrapy.Request(url="https://espressolab.com" + url_path, callback=self.parse_store_page)

    def parse_store_page(self, response: http.HtmlResponse):
        name = response.xpath("//h1/text()").get()
        address = extract_text(response.xpath("//div[contains(@class, 'address')]").get())
        latitude, longitude = extract_coords(response.xpath("/html/head/script[7]/text()").get())

        item = {
            "ref": response.url.split("/")[-2],
            "name": name,
            "addr_full": address,
            "lat": latitude,
            "lon": longitude,
        }

        apply_category(Categories.COFFEE_SHOP, item)

        yield item


def extract_text(address_element: str | None) -> str | None:
    if address_element is None:
        return None
    node = etree.fromstring(address_element)
    return clean_address("".join(node.itertext()).strip())


def extract_coords(script: str) -> tuple[float, float] | None:
    coords = MAP_SCRIPT_REGEX.findall(script)[0]
    return float(coords[0]), float(coords[1])
