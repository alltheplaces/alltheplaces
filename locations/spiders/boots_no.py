from html import unescape
from typing import Iterable
from urllib.parse import urlparse

from scrapy import Spider
from scrapy.http import Request, Response, TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature


class BootsNOSpider(Spider):
    name = "boots_no"
    item_attributes = {"brand": "Boots", "brand_wikidata": "Q6123139"}
    allowed_domains = ["apotek.boots.no", "zpin.it"]
    start_urls = ["https://zpin.it/on/location/map/boots/ajax/search.php?&c[z%3Acat%3AALL]=1&q=&lang=no&mo=440558&json"]

    def parse(self, response: TextResponse, **kwargs):
        if data := response.json():
            relations = data.get("relations")

            for store in relations.get("440558"):
                pin = store.get("pin")
                if pinId := pin.get("id"):
                    url = f"https://zpin.it/on/location/map/boots/ajax/company.php?id={pinId}&lang=no&mo=440558"
                    yield Request(url, callback=self.parse_store, cb_kwargs={"pin": pin})

    def parse_store(self, response: Response, pin: dict) -> Iterable[Feature]:
        item = Feature()

        item["ref"] = pin.get("id")

        if name := pin.get("name"):
            item["name"] = name
            item["branch"] = name.removeprefix("Boots Apotek").removeprefix("Boots apotek").strip()

        if website := response.css("h1 a::attr(href)").get():
            item["website"] = response.urljoin(website.strip())

        if latlng := pin.get("latlng"):
            item["lat"] = latlng.get("lat")
            item["lon"] = latlng.get("lng")

        if addr_full := response.css(".Zaddress").xpath("text()").getall():
            item["addr_full"] = addr_full

        extract_phone(item, response)
        extract_email(item, response)

        apply_category(Categories.PHARMACY, item)

        yield item


def extract_phone(item: Feature, selector: Response) -> None:
    for link in selector.xpath(".//a/@href").getall():
        link = unescape(link.strip())
        if link.startswith("tel:"):
            if number := urlparse(link).path or urlparse(link).netloc:
                item["phone"] = number
            return


def extract_email(item: Feature, selector: Response) -> None:
    for link in selector.xpath(".//a/@href").getall():
        link = unescape(link.strip())
        if link.startswith("mailto:") and "@" in link:
            item["email"] = urlparse(link).path
            return
