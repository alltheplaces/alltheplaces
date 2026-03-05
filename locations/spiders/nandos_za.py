from typing import Iterable
from urllib.parse import urljoin

from scrapy.http import TextResponse

from locations.categories import Extras, apply_yes_no
from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.nandos import NANDOS_SHARED_ATTRIBUTES


class NandosZASpider(JSONBlobSpider):
    name = "nandos_za"
    item_attributes = NANDOS_SHARED_ATTRIBUTES
    allowed_domains = ["api.locationbank.net"]
    start_urls = [
        "https://api.locationbank.net/storelocator/StoreLocatorAPI?clientId=67b9c5e4-6ddf-4856-b3c0-cf27cfe53255"
    ]
    web_root = "https://store.nandos.co.za/details/"
    locations_key = "locations"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["phone"] = item["phone"] = "; ".join(
            filter(None, [feature.get("primaryPhone"), feature.get("additionalPhone1")])
        )
        item["state"] = feature.get("administrativeArea")
        item["website"] = urljoin(self.web_root, feature.get("storeLocatorDetailsShortURL"))
        item["street_address"] = merge_address_lines([feature.get("addressLine1"), feature.get("addressLine2")])
        item["branch"] = item.pop("name").replace(self.item_attributes["brand"], "").strip()
        item["opening_hours"] = self.parse_opening_hours(feature.get("regularHours", []))

        apply_yes_no(Extras.BACKUP_GENERATOR, item, "Generator" in feature["slAttributes"])
        apply_yes_no(Extras.DELIVERY, item, "Delivery" in feature["slAttributes"])
        apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive Thru" in feature["slAttributes"])
        apply_yes_no(Extras.HALAL, item, "Halaal" in feature["slAttributes"])
        apply_yes_no(Extras.KOSHER, item, "Kosher" in feature["slAttributes"])
        apply_yes_no(Extras.TAKEAWAY, item, "Collect" in feature["slAttributes"])
        apply_yes_no(Extras.WIFI, item, "WiFi" in feature["slAttributes"])
        # Unhandled: "Alcohol License", "Dine In"

        yield item

    def parse_opening_hours(self, rules: list[dict]) -> OpeningHours:
        opening_hours = OpeningHours()
        for rule in rules:
            if day := sanitise_day(rule["openDay"]):
                opening_hours.add_range(day, rule["openTime"], rule["closeTime"])
        return opening_hours
