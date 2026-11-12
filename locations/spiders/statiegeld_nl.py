import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class StatiegeldNLSpider(JSONBlobSpider):
    name = "statiegeld_nl"
    item_attributes = {"country": "NL"}
    allowed_domains = ["geoserver-statiegeld.webgis.nl"]
    start_urls = [
        "https://geoserver-statiegeld.webgis.nl/Statiegeld/wfs?service=WFS&version=1.0.0&request=GetFeature&srsName=EPSG:4326&typeName=Statiegeld:inleverpunten&maxFeatures=50000&outputFormat=application/json"
    ]
    locations_key = "features"
    custom_settings = {"DOWNLOAD_TIMEOUT": 120}

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("properties"))

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["id"])
        item["name"] = feature["bedrijf"]
        if feature["straat_huisnr"] != "None":
            item["street_address"] = feature["straat_huisnr"]

        if match := re.fullmatch(r"(\d{4})\s?([A-Za-z]{2})\s+(.+)", feature["postcode_plaats"]):
            item["postcode"] = f"{match[1]} {match[2].upper()}"
            item["city"] = match[3]
        elif match := re.fullmatch(r"\d{4}\s+(.+)", feature["postcode_plaats"]):
            item["city"] = match[1]

        opening_hours = OpeningHours()
        for day, source_day in zip(DAYS, ("ma", "di", "woe", "do", "vrij", "za", "zo")):
            hours = feature[source_day]
            if hours == "Gesloten":
                opening_hours.set_closed(day)
            elif hours == "24 uur geopend":
                opening_hours.add_range(day, "00:00", "24:00")
            elif hours != "NA":
                for hours_range in hours.split(", "):
                    opening_hours.add_range(day, *hours_range.split("–"))
        if opening_hours:
            item["opening_hours"] = opening_hours

        apply_category(Categories.RECYCLING, item)
        apply_yes_no("recycling:plastic_bottles", item, feature["groot_pet"] == "Ja" or feature["klein_pet"] == "Ja")
        apply_yes_no("recycling:cans", item, feature["blik"] == "Ja")
        apply_yes_no("recycling:glass_bottles", item, feature["glas"] == "Ja")
        yield item
