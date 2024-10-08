from typing import Iterable

from locations.categories import Extras, apply_yes_no
from locations.items import Feature, set_closed
from locations.storefinders.yext_search import YextSearchSpider


class ChickFilASpider(YextSearchSpider):
    name = "chick_fil_a"
    item_attributes = {"brand": "Chick-fil-A", "brand_wikidata": "Q491516"}

    def parse_item(self, location: dict, item: Feature) -> Iterable[Feature]:
        self.crawler.stats.inc_value("z/c_conceptCode/{}".format(location["profile"].get("c_conceptCode")))
        self.crawler.stats.inc_value("z/c_locationFormat/{}".format(location["profile"].get("c_locationFormat")))

        status = location["profile"].get("c_status")

        if status == "CLOSED":
            set_closed(item)
        elif status == "FUTURE":
            return None
        elif status == "TEMPORARY_CLOSE":
            item["opening_hours"] = "off"

        if start := location["profile"].get("c_openMonth"):
            item["extras"]["start_date"] = "{:04}-{:02}-{:02}".format(start["year"], start["month"], start["day"])

        if ext := location["profile"].get("c_zipExtension"):
            item["postcode"] = "{}-{}".format(item["postcode"], ext)

        apply_yes_no(Extras.TAKEAWAY, item, location["profile"].get("c_carryout") is True)
        apply_yes_no(Extras.DELIVERY, item, location["profile"].get("c_delivery") is True)
        apply_yes_no(Extras.DRIVE_THROUGH, item, location["profile"].get("c_hasDriveThru") is True)
        apply_yes_no(Extras.INDOOR_SEATING, item, location["profile"].get("c_fullDineIn") is True)
        apply_yes_no(Extras.TAKEAWAY, item, location["profile"].get("c_carryout") is True)

        item["branch"] = location["profile"].get("c_locationName")

        yield item
