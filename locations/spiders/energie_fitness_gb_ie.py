from typing import Any

import scrapy
from scrapy.http import Response

from locations.dict_parser import DictParser


class EnergieFitnessGBIESpider(scrapy.Spider):
    name = "energie_fitness_gb_ie"
    item_attributes = {"brand": "énergie Fitness", "brand_wikidata": "Q109855553"}
    start_urls = ["https://www.energiefitness.com/api/locations"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["items"]:
            item = DictParser.parse(location["customProperties"]["locationDetails"]["contactDetails"])
            item["branch"] = item.pop("name").replace("Energie Fitness ", "")
            item["website"] = response.urljoin(location["urlPath"])
            yield item
