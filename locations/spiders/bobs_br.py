import re

from scrapy import Selector, Spider

from locations.items import Feature


class BobsBRSpider(Spider):
    name = "bobs_br"
    item_attributes = {"brand": "Bob's", "brand_wikidata": "Q1392113"}
    start_urls = ["https://bobs.com.br/onde-tem-bobs"]
    no_refs = True

    def parse(self, response, **kwargs):
        for lat, lon, popup in re.findall(
            r"L\.marker\({ lat: '(-?\d+.\d+)', lng: '(-?\d+.\d+)'.+?bindPopup\(\"(.+?)\",", response.text, re.DOTALL
        ):
            item = Feature()
            item["lat"] = lat
            item["lon"] = lon

            sel = Selector(text=popup)

            item["name"] = sel.xpath('//span[@class="marker_popup_content_title"]/text()').get()
            item["street_address"] = sel.xpath('//div[@class="marker_popup_content"]/text()').getall()[1]

            yield item
