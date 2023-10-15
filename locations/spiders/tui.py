import logging
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import DAYS_PL, OpeningHours


class TUISpider(Spider):
    name = "tui"
    item_attributes = {"brand": "TUI", "brand_wikidata": "Q573103"}
    start_urls = ["https://www.tui.pl/api/www/office"]
    countries = {"Czechy": "CZ", "Litwa": "LT", "Polska": "PL", "Słowacja": "SK", "Ukraina": "UA"}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for country in response.json()["countries"]:
            countryName = country["option"]["value"]
            if countryName not in self.countries:
                logging.error(f"Unsupported countryName: {countryName}")
                continue
            countryCode = self.countries[countryName]
            for region in country["regions"]:
                for city in region["cities"]:
                    for office in city["offices"]:
                        item = DictParser.parse(office)
                        item["country"] = countryCode
                        if (
                            "position" in office
                            and "latitude" in office["position"]
                            and "longitude" in office["position"]
                        ):
                            item["lat"] = office["position"]["latitude"]
                            item["lon"] = office["position"]["longitude"]
                        if "program" in office:
                            openingHours = OpeningHours()
                            for hours in office["program"].split("<br>"):
                                openingHours.add_ranges_from_string(ranges_string=hours, days=DAYS_PL)
                            item["opening_hours"] = openingHours
                        yield item
