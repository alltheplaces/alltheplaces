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
            country_name = country["option"]["value"]

            if country_name not in self.countries:
                logging.error(f"Unsupported country_name: {country_name}")
                continue

            country_code = self.countries[country_name]
            for region in country["regions"]:
                for city in region["cities"]:
                    for office in city["offices"]:
                        item = DictParser.parse(office)

                        item["street_address"] = item.pop("street", None)
                        item["country"] = country_code

                        if (
                            "position" in office
                            and "latitude" in office["position"]
                            and "longitude" in office["position"]
                        ):
                            item["lat"] = office["position"]["latitude"]
                            item["lon"] = office["position"]["longitude"]

                        if "program" in office:
                            opening_hours = OpeningHours()
                            for hours in office["program"].split("<br>"):
                                opening_hours.add_ranges_from_string(ranges_string=hours, days=DAYS_PL)
                            item["opening_hours"] = opening_hours

                        yield item
