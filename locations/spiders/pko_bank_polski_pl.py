import logging

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import point_locations
from locations.hours import DAYS_PL, DELIMITERS_PL, OpeningHours


class PKOBankPolskiPLSpider(Spider):
    name = "pko_bank_polski_pl"
    item_attributes = {"brand": "PKO Bank Polski", "brand_wikidata": "Q578832"}

    def start_requests(self):
        for lat, lon in point_locations("eu_centroids_20km_radius_country.csv", "PL"):
            startLat = int(float(lat) * 10 - 0.5)
            startLon = int(float(lon) * 10 - 0.5)
            bounds = ",".join([str(c) for c in [startLat, startLon, startLat + 1, startLon + 1]])
            yield JsonRequest(
                url=f"https://www.pkobp.pl/poi/?type=facility,atm&search=&bounds={bounds}",
            )

    def parse(self, response):
        for location in response.json()["result"]:
            item = DictParser.parse(location)
            if location["type"] == "atm":
                apply_category(Categories.ATM, item)
            elif location["type"] == "facility":
                apply_category(Categories.BANK, item)
            else:
                logging.error(f"Unexpected type: {location['type']}")
            if "opening_hours" in location:
                if location["opening_hours"] == "Codziennie przez całą dobę":
                    item["opening_hours"] = "24/7"
                else:
                    item["opening_hours"] = OpeningHours()
                    for line in location["opening_hours"].split("<br />"):
                        item["opening_hours"].add_ranges_from_string(
                            ranges_string=line, days=DAYS_PL, delimiters=DELIMITERS_PL
                        )
            yield item
