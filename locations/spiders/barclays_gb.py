from typing import Any
from urllib.parse import urljoin

import scrapy
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class BarclaysGBSpider(scrapy.Spider):
    name = "barclays_gb"
    item_attributes = {"brand": "Barclays", "brand_wikidata": "Q245343"}

    def start_requests(self):
        for city in city_locations("GB", 10000):
            url = f'https://search.barclays.co.uk/content/bf/en/4_0/branches_atms?lat={city["latitude"]}&lng={city["longitude"]}'
            yield JsonRequest(url=url, callback=self.parse)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = response.json()
        for branch in data.get("branches", []):
            yield self.parse_location(branch, is_atm=False)

        for atm in data.get("atms", []):
            yield self.parse_location(atm, is_atm=True)

    def parse_location(self, location_data: dict, is_atm: bool) -> Feature:
        item = DictParser.parse(location_data)
        item["ref"] = f'{location_data["outletId"]} - {"ATM" if is_atm else "Bank"}'
        item["branch"] = item.pop("name", None)
        item["street_address"] = merge_address_lines(
            [location_data["address"].get("line1", ""), location_data["address"].get("line2", "")]
        )
        item["website"] = urljoin("https://www.barclays.co.uk", item.get("website", ""))
        apply_category(Categories.ATM if is_atm else Categories.BANK, item)

        item["opening_hours"] = OpeningHours()
        for day, time in location_data.get("openingHours", {}).items():
            if isinstance(time, list):
                continue
            open_time = time.get("openTime")
            close_time = time.get("closeTime")
            if open_time == "00:00" and close_time == "00:00":
                item["opening_hours"].set_closed(day)
            else:
                item["opening_hours"].add_range(day=day, open_time=open_time, close_time=close_time)

        return item
