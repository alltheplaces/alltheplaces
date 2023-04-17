import re

import chompjs
from scrapy import Selector, Spider

from locations.items import Feature


def strip_cdata(data: str) -> str:
    return data.replace(" //<![CDATA[", "").replace("//]]>", "")


class JasmilSpider(Spider):
    name = "jasmil"
    item_attributes = {"brand": "Jasmil", "brand_wikidata": "Q117309207"}
    start_urls = [
        "https://rs.jasmil.com/prodavnice",
        "https://me.jasmil.com/prodavnice",
        "https://ba.jasmil.com/prodavnice",
        "https://mk.jasmil.com/prodavnice",
    ]

    def parse(self, response, **kwargs):
        country = re.match(r"https://(\w\w)\.", response.url).group(1).upper()
        for html, lat, lon in chompjs.parse_js_object(
            strip_cdata(response.xpath('//script[contains(text(), "var markers")]/text()').get())
        ):
            sel = Selector(text=html)
            item = Feature()
            item["lat"] = lat
            item["lon"] = lon

            item["name"] = sel.xpath("//h3/text()").get()
            item["website"] = item["ref"] = sel.xpath('//a[contains(@href, "https")]/@href').get()
            if phone := sel.xpath('//a[contains(@href, "tel")]/@href').get():
                item["phone"] = phone.replace("/", "")
            item["addr_full"] = sel.xpath("//p/text()").get()
            item["country"] = country

            yield item
