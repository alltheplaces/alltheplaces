import pprint
from typing import Any

import pyproj
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature


class PostenNOSpider(Spider):
    name = "posten_no"
    item_attributes = {"brand": "Posten", "brand_wikidata": "Q1815701"}
    start_urls = ["https://www.posten.no/en/map/_/service/no.posten.map/enonicUnits?country=NO"]

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

            for rules in attributes["apningstider"]:
                if rules["name"] != "openingHoursLabel":
                    continue

                item["opening_hours"] = self.parse_opening_hours(rules)
                break

            if attributes["enhetstype"] in (1, 21):
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
            else:
                self.logger.error("Unexpected type: {}".format(attributes["enhetstype"]))

            yield item

    def parse_opening_hours(self, rules: dict) -> OpeningHours:
        oh = OpeningHours()
        for day, rule in rules["perDay"].items():
            if rule["ErDognApent"] is True:
                pprint.pp(rule)
                oh.add_range(day, "00:00", "24:00")
            else:
                for times in rule["content"].split(", "):
                    oh.add_range(day, *times.split("–"), time_format="%H.%M")
        return oh
