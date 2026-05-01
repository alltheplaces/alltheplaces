from typing import Any

from pyproj import Transformer
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature

PAKKEBOKSEN = {"brand": "Pakkeboksen", "brand_wikidata": "Q12309164"}


class BringDKSpider(Spider):
    name = "bring_dk"
    start_urls = ["https://www.bring.dk/en/map/_/service/no.posten.map/enonicUnits?country=DK&englishData=true"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        transformer = Transformer.from_crs(25832, 4326)
        for location in response.json()["units"]:
            attributes = location["attributes"]
            item = Feature()
            item["lat"], item["lon"] = transformer.transform(location["geometry"]["x"], location["geometry"]["y"])
            item["ref"] = attributes["enhetsnr"]
            item["website"] = "https://www.bring.dk/en/map?ID={}".format(attributes["enhetsnr"])
            item["name"] = attributes["navn"]
            item["street_address"] = attributes["besoksadresse"]
            item["city"] = attributes["besoksadresse_poststed"]
            item["postcode"] = attributes["besoksadresse_postnr"]

            if attributes["enhetstype"] == 43:
                apply_category(Categories.PARCEL_LOCKER, item)
                item.update(PAKKEBOKSEN)
            elif attributes["enhetstype"] == 26:
                apply_category(Categories.GENERIC_POI, item)
                item["extras"]["post_office"] = "post_partner"
                item["extras"]["post_office:brand"] = "Bring"

            for rules in attributes["apningstider"]:
                if rules["type"] != 1000:
                    continue
                oh = OpeningHours()
                for day, rule in rules["perDay"].items():
                    oh.add_range(day, *rule["content"].split("–"), time_format="%H.%M")
                item["opening_hours"] = oh
                break

            yield item
