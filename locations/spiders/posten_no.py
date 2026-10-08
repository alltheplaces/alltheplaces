import re
from itertools import groupby
from typing import Any

import pyproj
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class PostenNOSpider(Spider):
    name = "posten_no"
    item_attributes = {"brand": "Posten", "brand_wikidata": "Q1815701"}
    # Red letter boxes are only included when asked for.
    start_urls = [
        "https://www.posten.no/en/map/_/service/no.posten.map/enonicUnits?country=NO&includeRedMailBoxes=true"
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        transformer = pyproj.Transformer.from_crs(25833, 4326)
        for location in response.json()["units"]:
            attributes = location["attributes"]

            item = Feature()
            item["ref"] = item["extras"]["ref:posten"] = attributes["enhetsnr"]
            item["lat"], item["lon"] = transformer.transform(location["geometry"]["x"], location["geometry"]["y"])

            # item["extras"]["fixme:description"] = attributes["beliggenhet"]
            item["name"] = attributes["navn"]
            item["street_address"] = attributes["besoksadresse"]
            item["postcode"] = attributes["besoksadresse_postnr"]
            item["city"] = attributes["besoksadresse_poststed"]

            item["website"] = item["extras"]["website:no"] = "https://www.posten.no/kart?ID={}".format(item["ref"])
            item["extras"]["website:en"] = "https://www.posten.no/en/map?ID={}".format(item["ref"])

            for rules in attributes.get("apningstider") or []:
                if rules["name"] != "openingHoursLabel":
                    continue

                try:
                    item["opening_hours"] = self.parse_opening_hours(rules)
                except:
                    self.logger.error("Error parsing opening hours")

                break

            if attributes["enhetstype"] in (1, 21, 32):
                apply_category(Categories.POST_OFFICE, item)
                item["extras"]["post_office"] = "bureau"
            elif attributes["enhetstype"] == 4:
                apply_category(Categories.GENERIC_POI, item)
                item["extras"]["post_office"] = "post_partner"
            elif attributes["enhetstype"] == 19:
                apply_category(Categories.GENERIC_POI, item)
                item["extras"]["post_office"] = "post_partner"
                apply_yes_no("post_office:parcel_pickup", item, True)
            elif attributes["enhetstype"] == 37:
                apply_category(Categories.PARCEL_LOCKER, item)
            elif attributes["enhetstype"] == 10:
                apply_category(Categories.POST_BOX, item)
                if collection_times := self.parse_collection_times(attributes.get("deadlines") or []):
                    item["extras"]["collection_times"] = collection_times
            else:
                item["extras"]["enhetstype"] = str(attributes["enhetstype"])
                self.logger.error("Unexpected type: {}".format(attributes["enhetstype"]))
            yield item

    @staticmethod
    def parse_collection_times(deadlines: list[dict]) -> str:
        # Each deadline is a collection time ("1400") on a set of weekdays ("1,2,3,4,5", 1 = Monday).
        times = {}
        for deadline in deadlines:
            time = deadline.get("dateTime") or ""
            if not re.fullmatch(r"\d{4}", time):
                continue
            for day in str(deadline.get("periodDays") or "").split(","):
                if day.strip().isdigit() and 1 <= int(day) <= 7:
                    times.setdefault(DAYS[int(day) - 1], set()).add(f"{time[:2]}:{time[2:]}")
        by_day = {day: ",".join(sorted(day_times)) for day, day_times in times.items()}
        collection_times = []
        for time, days in groupby(DAYS, key=by_day.get):
            if time:
                days = list(days)
                collection_times.append(f"{days[0]}-{days[-1]} {time}" if len(days) > 1 else f"{days[0]} {time}")
        return "; ".join(collection_times)

    def parse_opening_hours(self, rules: dict) -> OpeningHours:
        oh = OpeningHours()
        for day, rule in rules["perDay"].items():
            if rule["content"] == "open24H":
                oh.add_range(day, "00:00", "24:00")
            else:
                for times in rule["content"].split(", "):
                    oh.add_range(day, *times.split("–"), time_format="%H.%M")
        return oh
