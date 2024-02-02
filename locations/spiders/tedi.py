import logging
from typing import Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.geo import point_locations
from locations.hours import DAYS, OpeningHours


class TediSpider(Spider):
    name = "tedi"
    item_attributes = {"brand": "TEDi", "brand_wikidata": "Q1364603"}
    countries = ["AT", "BG", "CZ", "DE", "ES", "HR", "HU", "IT", "PL", "PT", "RO", "SI", "SK"]

    def start_requests(self) -> Iterable[Request]:
        for country in self.countries:
            for lat, lon in point_locations("eu_centroids_20km_radius_country.csv", country):
                culture = country.lower()
                yield Request(
                    f"https://storeviewer-phkw2veu6jdfq.azureedge.net/StoreFinder/search?lat={lat}&lng={lon}&culture={culture}",
                    cb_kwargs=dict(country=country),
                )

    def parse(self, response: Response, **kwargs):
        country = kwargs["country"]
        for store in response.json()["stores"]:
            item = DictParser.parse(store)
            if item["country"] != country:
                if item["country"] not in self.countries:
                    logging.info(f"Missing country {item['country']} in country array")
                continue
            item["opening_hours"] = OpeningHours()
            for oh in store["openingHour"]["intervals"]:
                item["opening_hours"].add_days_range(days=DAYS[:6], open_time=oh["start"], close_time=oh["end"])
            item["website"] = item["website"].replace("\\", "/")
            yield item
