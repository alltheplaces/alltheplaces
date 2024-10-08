from typing import Any

import scrapy
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class TherapieClinicSpider(scrapy.Spider):
    name = "therapie_clinic"
    item_attributes = {"brand": "Thérapie Clinic", "brand_wikidata": "Q123034602"}
    start_urls = ["https://therapieclinic.com/api/clinic/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["locations"]:
            place = self.get_primary(location["places"])
            item = DictParser.parse(place)
            item["street_address"] = merge_address_lines(
                [place["address"]["streetAddress1"], place["address"]["streetAddress2"]]
            )
            item["ref"] = location["id"]
            item["branch"] = place["officeName"]
            item["lat"] = place["address"]["latitude"]
            item["lon"] = place["address"]["longitude"]
            item["phone"] = self.get_primary(place["phones"]).get("number")

            item["opening_hours"] = OpeningHours()
            for rule in self.get_primary(place["businessHours"]).get("timePeriods") or []:
                if rule["closed"] is True:
                    item["opening_hours"].set_closed(rule["openDay"])
                elif rule["closed"] is True:
                    item["opening_hours"].add_range(rule["openDay"], "00:00", "24:00")
                else:
                    item["opening_hours"].add_range(rule["openDay"], rule["openTime"], rule["closeTime"])

            yield item

    def get_primary(self, entries: [dict]) -> dict:
        for entry in entries or []:
            if entry.get("primary") is True:
                return entry
        return {}
