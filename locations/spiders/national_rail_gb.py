import string
from typing import Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.items import Feature


class NationalRailGBSpider(Spider):
    name = "national_rail_gb"
    item_attributes = {"extras": {"network": "National Rail", "network:wikidata": "Q26334"}}

    operators = {
        "AW": ("Transport for Wales", "Q104878180"),
        "CC": ("c2c", None),
        "CH": ("Chiltern Railways", None),
        "EM": ("East Midlands Railway", None),
        "GM": ("Transport for Greater Manchester", None),
        "GN": ("Great Northern", None),
        "GR": ("LNER", None),
        "GW": ("Great Western Railway", "Q1419438"),
        "GX": ("Gatwick Express", None),
        "HX": ("Heathrow Express", None),
        "IL": ("Island Line", None),
        "LE": ("Greater Anglia", None),
        "LN": ("London Northwestern Railway", None),
        "LO": ("London Overground", None),
        "LT": ("London Underground", None),
        "ME": ("Merseyrail", None),
        "NR": ("Network Rail", None),
        "NT": ("Northern", "Q85789775"),
        "SE": ("Southeastern", "Q1696490"),
        "SN": ("Southern", None),
        "SR": ("ScotRail", "Q18356161"),
        "SW": ("South Western Railway", None),
        "TL": ("Thameslink", None),
        "TP": ("TransPennine Express", None),
        "VT": ("Avanti West Coast", None),
        "WM": ("West Midlands Railway", None),
        "XP": ("Glasgow Prestwick Airport Ltd", None),
        "XR": ("Elizabeth line", None),
        "XS": ("London Southend Airport", None),
    }

    def start_requests(self) -> Iterable[Request]:
        for letter in string.ascii_uppercase:
            yield JsonRequest(
                url="https://stationpicker.nationalrail.co.uk/stationPicker/{}".format(letter),
                headers={"Origin": "https://www.nationalrail.co.uk"},
            )

    def parse(self, response, **kwargs):
        for location in response.json()["payload"]["stations"]:
            if location["classification"] != "NORMAL":
                continue
            if not location["operator"]:
                continue

            item = Feature()
            item["ref"] = item["extras"]["ref:crs"] = location["crsCode"]
            item["name"] = location["name"]
            item["lat"] = location["latitude"]
            item["lon"] = location["longitude"]
            item["postcode"] = location["postcode"]
            item["website"] = "https://www.nationalrail.co.uk/stations/{}/".format(location["crsCode"].lower())
            item["operator"], item["operator_wikidata"] = self.operators.get(
                location["operator"], (location["operator"], None)
            )

            apply_category(Categories.TRAIN_STATION, item)

            yield item
