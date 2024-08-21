import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response
from unidecode import unidecode

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS, DAYS_PL, OpeningHours


class TuiSpider(Spider):
    name = "tui"
    item_attributes = {"brand": "TUI", "brand_wikidata": "Q573103", "extras": Categories.SHOP_TRAVEL_AGENCY.value}
    start_urls = ["https://www.tui.pl/api/services/tui-cms/api/offices/offices?market=pl&locale=pl"]
    countries = {
        "Česká republika": "CZ",
        "Czechy": "CZ",
        "Litwa": "LT",
        "Polska": "PL",
        "Słowacja": "SK",
        "Ukraina": "UA",
    }
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for country in response.json()["countries"]:
            country_name = country["option"]["value"]

            if country_name not in self.countries:
                self.logger.error(f"Unsupported country name in API response: {country_name}")
                continue

            for region in country["regions"]:
                for city in region["cities"]:
                    for office in city["offices"]:
                        yield from self.parse_office(office) or []

    def parse_office(self, office: dict) -> Any:
        office["street_address"] = office.pop("address", None)
        office["country"] = self.countries[office["country"]]

        item = DictParser.parse(office)

        city_urlsafe = unidecode(re.sub(r"\W+", "-", office["city"].lower()))
        street_address_urlsafe = unidecode(re.sub(r"\W+", "-", office["street_address"].lower()))
        item["website"] = f"https://www.tui.pl/kontakt/biura-tui/{city_urlsafe}/{street_address_urlsafe}/{office['id']}"

        if oh_array := office.get("openingHours"):
            hours_string = " ".join(oh_array or [])
            for day_number, day_name in enumerate(DAYS):
                hours_string = hours_string.replace(str(day_number), f"{day_name}:")
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)
        elif office.get("program"):
            hours_string = office["program"].strip().replace("<br>", " ")
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string, days=DAYS_PL)

        yield item
