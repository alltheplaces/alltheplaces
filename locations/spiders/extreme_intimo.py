import re

from chompjs import chompjs
from scrapy import Selector, Spider

from locations.items import Feature
from locations.spiders.jasmil import strip_cdata


class ExtremeIntimoSpider(Spider):
    name = "extreme_intimo"
    item_attributes = {"brand": "Extreme Intimo", "brand_wikidata": "Q117309408"}
    start_urls = [
        "https://rs.extremeintimo.com/prodavnice",
        "https://hr.extremeintimo.com/prodavnice",
        "https://si.extremeintimo.com/prodavnice",
        "https://me.extremeintimo.com/prodavnice",
        "https://ba.extremeintimo.com/prodavnice",
        "https://mk.extremeintimo.com/prodavnice",
        "https://cz.extremeintimo.com/prodavnice",
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
