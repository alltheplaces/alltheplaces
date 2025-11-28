import json

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class PodPointSpider(Spider):
    name = "pod_point"
    item_attributes = {"operator": "Pod Point", "operator_wikidata": "Q42888154"}
    start_urls = ["https://charge.pod-point.com/"]

    def parse(self, response, **kwargs):
        for location in json.loads(
            response.xpath('//script[contains(text(), "podAddresses")]/text()').re_first(
                r"var podAddresses = (\[.+\]);"
            )
        ):
            item = DictParser.parse(location)
            item["email"] = None  # Seems to be redacted personal info
            item["extras"]["capacity"] = location["pod_count"]

            apply_category(Categories.CHARGING_STATION, item)

            yield item
