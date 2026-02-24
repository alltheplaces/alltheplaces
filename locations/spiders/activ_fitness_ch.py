import json
import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.dict_parser import DictParser


class ActivFitnessCHSpider(Spider):
    name = "activ_fitness_ch"
    item_attributes = {"brand": "Activ Fitness", "brand_wikidata": "Q123747318"}
    start_urls = ["https://www.activfitness.ch/en/map/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = re.search(
            r"filialfinderData\s*=\s*(\[.*\]);\s* ",
            response.xpath('//*[contains(text(),"filialfinderData")]/text()').get(),
        ).group(1)
        for location in json.loads(raw_data):
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full")
            item["branch"] = item.pop("name").removeprefix("Activ Fitness ")
            yield item
