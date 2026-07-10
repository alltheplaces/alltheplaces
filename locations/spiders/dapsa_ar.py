import re
from typing import Iterable

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.items import Feature
from locations.storefinders.storepoint import StorepointSpider


class DapsaARSpider(StorepointSpider):
    name = "dapsa_ar"
    item_attributes = {"brand": "Dapsa"}  # no Wikidata/NSI entry for this Argentine fuel brand
    key = "163ea721fda366"

    def parse_item(self, item: Feature, location: dict, **kwargs) -> Iterable[Feature]:
        # The helper mapped "streetaddress" to addr_full, but that field is actually "<city>, <province>,
        # ARGENTINA"; the real street line is in "description".
        item.pop("addr_full", None)
        item["street_address"] = location.get("description")
        locality = [part.strip() for part in (location.get("streetaddress") or "").split(",")]
        if locality:
            item["city"] = locality[0]
        if len(locality) >= 3:
            item["state"] = locality[1]

        if branch := item.pop("name", None):
            item["branch"] = re.sub(r"^DAPSA\s+", "", branch).strip() or None

        apply_category(Categories.FUEL_STATION, item)

        tags = [tag.strip().lower() for tag in (location.get("tags") or "").split(",")]
        apply_yes_no(Fuel.CNG, item, "gnc" in tags)  # GNC = gas natural comprimido
        apply_yes_no(Extras.CAR_WASH, item, "lavado" in tags)
        apply_yes_no(Extras.COMPRESSED_AIR, item, "aire" in tags)
        apply_yes_no(Extras.WIFI, item, "wifi" in tags or "wiffi" in tags)
        apply_yes_no(Extras.ATM, item, any("cajero" in tag for tag in tags))
        if "24hs" in tags:
            item["opening_hours"] = "24/7"

        yield item
