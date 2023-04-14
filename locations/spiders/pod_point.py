import chompjs
from scrapy import Spider

from locations.dict_parser import DictParser


class PodPointSpider(Spider):
    name = "pod_point"
    item_attributes = {"brand": "Pod Point", "brand_wikidata": "Q42888154"}
    start_urls = ["https://charge.pod-point.com/"]

    def parse(self, response, **kwargs):
        data = chompjs.parse_js_object(response.xpath('//script[contains(text(), "podAddresses")]/text()').get())
        for location in data:
            item = DictParser.parse(location)
            item["email"] = None  # Seems to be redacted personal info
            item["extras"]["capacity"] = location["pod_count"]

            yield item
