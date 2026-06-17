from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Extras, apply_yes_no
from locations.items import Feature
from locations.spiders.nandos import NANDOS_SHARED_ATTRIBUTES
from locations.storefinders.location_bank import LocationBankSpider


class NandosZASpider(LocationBankSpider):
    name = "nandos_za"
    item_attributes = NANDOS_SHARED_ATTRIBUTES
    client_id = "67b9c5e4-6ddf-4856-b3c0-cf27cfe53255"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        apply_yes_no(Extras.BACKUP_GENERATOR, item, "Generator" in feature["slAttributes"])
        apply_yes_no(Extras.DELIVERY, item, "Delivery" in feature["slAttributes"])
        apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive Thru" in feature["slAttributes"])
        apply_yes_no(Extras.HALAL, item, "Halaal" in feature["slAttributes"])
        apply_yes_no(Extras.KOSHER, item, "Kosher" in feature["slAttributes"])
        apply_yes_no(Extras.TAKEAWAY, item, "Collect" in feature["slAttributes"])
        apply_yes_no(Extras.WIFI, item, "WiFi" in feature["slAttributes"])
        # Unhandled: "Alcohol License", "Dine In"

        yield item
