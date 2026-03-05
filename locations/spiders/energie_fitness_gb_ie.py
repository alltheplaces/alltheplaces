from typing import Any

import scrapy
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class EnergieFitnessGBIESpider(scrapy.Spider):
    name = "energie_fitness_gb_ie"
    item_attributes = {"brand": "énergie Fitness", "brand_wikidata": "Q109855553"}
    start_urls = ["https://www.energiefitness.com/api/locations"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["items"]:
            item = DictParser.parse(location["customProperties"]["locationDetails"]["contactDetails"])
            item["ref"] = location["id"]
            item["branch"] = item.pop("name").removeprefix("Energie Fitness ")
            item["street_address"] = merge_address_lines(
                [
                    location["customProperties"]["locationDetails"]["contactDetails"]["streetAddressLine1"],
                    location["customProperties"]["locationDetails"]["contactDetails"]["streetAddressLine2"],
                ]
            )
            item["website"] = response.urljoin(location["urlPath"])
            yield item
