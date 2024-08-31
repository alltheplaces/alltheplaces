import json
import re

from scrapy import Spider

from locations.dict_parser import DictParser


class RossmannTRSpider(Spider):
    name = "rossmann_tr"
    item_attributes = {"brand_wikidata": "Q316004"}
    start_urls = ["https://www.rossmann.com.tr/magazalar"]

    def parse(self, response, **kwargs):
        script = response.xpath(
            '//div/div[@data-pb-style="WQVBN6O"]/div[@data-content-type="html"]//script/text()'
        ).get()
        if match := re.search(r"var locations = (\[{.+}\]);$", script, re.MULTILINE):
            for location in json.loads(match.group(1)):
                location["id"] = location.pop("gmaps_id")
                location["address_region"] = location.pop("distinct")
                item = DictParser.parse(location)
                yield item
