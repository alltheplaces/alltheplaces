import re
from typing import Iterable

import scrapy
from scrapy import http
from locations.pipelines.address_clean_up import clean_address
from lxml import etree

STORES_PAGE_URL = "https://espressolab.com/subeler/"
WEBSITE_ROOT = "https://espressolab.com"
STORE_LINKS_XPATH = "/html/body/form/div[4]/div[4]/div[1]/div/div/div/div[1]/div/div/div[2]/ul/li/a/@href"
STORE_NAME_XPATH = "//h1/text()"
STORE_ADDRESS_XPATH = "//div[contains(@class, 'address')]"
MAP_SCRIPT_XPATH = "/html/head/script[7]/text()"
MAP_SCRIPT_REGEX = re.compile(r"google\.maps\.LatLng\([ ]*([-0-9.]*)[ ]*,[ ]*([-0-9.]*)[ ]*\);")

class EspressolabSpider(scrapy.Spider):
    name = "espressolab"
    item_attributes = {"brand": "Espressolab", "brand_wikidata": "Q97599059"}

    def start_requests(self) -> Iterable[scrapy.Request]:
        yield scrapy.Request(url=STORES_PAGE_URL, callback=self.parse_stores_page)

    def parse_stores_page(self, response: http.HtmlResponse):
        for url_path in response.xpath(STORE_LINKS_XPATH).getall():
            yield scrapy.Request(url=WEBSITE_ROOT + url_path, callback=self.parse_store_page)

    def parse_store_page(self, response: http.HtmlResponse):
        name = response.xpath(STORE_NAME_XPATH).get()
        address = extract_text(response.xpath(STORE_ADDRESS_XPATH).get())
        latitude, longitude = extract_coords(response.xpath(MAP_SCRIPT_XPATH).get())
        
        item = {
            "ref": response.url.split("/")[-2],
            "name": name,
            "addr_full": address,
            "lat": latitude,
            "lon": longitude,
        }

        yield item


def extract_text(address_element: str | None) -> str | None:
    if address_element is None:
        return None
    node = etree.fromstring(address_element)
    return clean_address("".join(node.itertext()).strip())

def extract_coords(script: str) -> tuple[float, float] | None:
    coords = MAP_SCRIPT_REGEX.findall(script)[0]
    return float(coords[0]), float(coords[1])
