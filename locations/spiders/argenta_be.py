from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class ArgentaBESpider(JSONBlobSpider):
    name = "argenta_be"
    item_attributes = {"brand": "Argenta", "brand_wikidata": "Q932856"}
    start_urls = ["https://www.argenta.be/content/argenta/nl/kantoren/_jcr_content.complete.nl.json"]
    locations_key = "offices"

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("general"))
        feature.update(feature.pop("officeAddress"))
        feature.update(feature.pop("officeContact"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature.get("officeNumber")
        item["housenumber"] = feature.get("houseNr")
        item["street"] = feature.get("localizedStreet")
        item["city"] = feature.get("localizedCity")
        item["state"] = feature.get("rpr")
        item["extras"]["addr:street:nl"] = feature["street"].get("languageDescription", {}).get("nl", {}).get("value")
        item["extras"]["addr:street:fr"] = feature["street"].get("languageDescription", {}).get("fr", {}).get("value")
        item["extras"]["addr:city:nl"] = feature["city"].get("languageDescription", {}).get("nl", {}).get("value")
        item["extras"]["addr:city:fr"] = feature["city"].get("languageDescription", {}).get("fr", {}).get("value")
        item["extras"]["website:nl"] = item["website"]
        item["extras"]["website:fr"] = item["website"].replace("/nl/kantoren/", "/fr/agences/")
        item["extras"]["fax"] = feature.get("formattedFax")

        apply_category(Categories.BANK, item)
        apply_yes_no(Extras.ATM, item, feature.get("atm"))
        yield item
