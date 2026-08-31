from typing import Any, Iterable

import scrapy
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class PpgPaintsSpider(scrapy.Spider):
    name = "ppg_paints"
    item_attributes = {"brand": "PPG Paints", "brand_wikidata": "Q83891559"}

    async def start(self) -> Iterable[Any]:
        for country in ["CA", "US", "MX"]:
            yield JsonRequest(
                url="https://app-brandstorelocatoruscprd-001.azurewebsites.net/api/location/GetFilteredLocations",
                data={
                    "latitude": 0,
                    "longitude": 0,
                    "maxNumberOfResults": 5000,
                    "filters": [
                        {"locationType": ["Dealer"], "countryCode": [country], "brand": ["PPG Paints"]},
                        {"locationType": ["PPC Store"], "countryCode": [country], "brand": ["PPG Paints"]},
                    ],
                },
            )

    def parse(self, response):
        for location in response.json():
            location.update(location.pop("location"))
            item = DictParser.parse(location)
            item["street_address"] = merge_address_lines([location])
            yield item
