import re
import scrapy
from locations.items import GeojsonPointItem
from scrapy.http import HtmlResponse


class JusticeSpider(scrapy.Spider):
    name = "justice"
    item_attributes = {"brand": "Justice"}
    allowed_domains = ["shopjustice.com"]
    start_urls = (
        "https://maps.shopjustice.com/api/getAsyncLocations?template=search&level=search&radius=50000&search=55401",
    )
    addr2regex = re.compile(r"^([A-Za-z\ \.]+)\, ([A-Z]+) ([0-9]+)$")

    def parse(self, response):
        data = response.json()
        stores = data["markers"]
        for store in stores:
            html = HtmlResponse(url="", body=store["info"].encode("UTF-8"))

            unp = {}
            unp["lat"] = store["lat"]
            unp["lon"] = store["lng"]

            if unp["lat"]:
                unp["lat"] = float(unp["lat"])
            if unp["lon"]:
                unp["lon"] = float(unp["lon"])

            unp["ref"] = store["locationId"]
            unp["addr_full"] = html.xpath(
                '//div[contains(@class, "addr")]/text()'
            ).extract_first()
            unp["phone"] = html.xpath(
                '//div[contains(@class, "phone")]/text()'
            ).extract_first()
            unp["name"] = html.xpath('//div[@class="loc-name"]/text()').extract_first()
            addr2 = html.xpath('//div[contains(@class, "csz")]/text()').extract_first()
            if addr2:
                addr2 = addr2.strip()
                three_pieces = self.addr2regex.search(addr2)
                if three_pieces:
                    city, state, zipcode = three_pieces.groups()
                    unp["city"] = city
                    unp["state"] = state
                    unp["postcode"] = zipcode

            properties = {}
            for key in unp:
                if unp[key]:
                    properties[key] = unp[key]

            yield GeojsonPointItem(**properties)
