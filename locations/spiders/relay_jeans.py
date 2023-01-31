import html

from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours, day_range, sanitise_day


class RelayJeansSpider(Spider):
    name = "relayjeans"
    item_attributes = {"brand": "Relay Jeans", "brand_wikidata": "Q116378360"}
    start_urls = [
        f"https://www.relayjeans.co.za/browse/storeLocatorSearch.jsp?searchText={letter}" for letter in "aeiou"
    ]

    def parse(self, response, **kwargs):
        for location in response.json()["items"]:
            location["street_address"] = html.unescape(
                ", ".join(
                    filter(
                        None,
                        [location.pop("address_line1"), location.pop("address_line2"), location.pop("address_line3")],
                    )
                )
            )
            location["phoneNumber"] = location["phoneNumber"].replace(",", ";")

            item = DictParser.parse(location)

            item["ref"] = location.pop("branch_number")
            item["name"] = location.pop("branch_name")

            item["opening_hours"] = OpeningHours()
            for rule in location["normalOpeningHours"]:
                if "-" in rule["description"]:
                    start_day, end_day = rule["description"].split(" - ")
                else:
                    start_day = end_day = rule["description"]
                for day in day_range(sanitise_day(start_day), sanitise_day(end_day)):
                    item["opening_hours"].add_range(day, rule["openTime"], rule["closeTime"])

            yield item
