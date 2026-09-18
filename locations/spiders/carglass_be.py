import re
from typing import Iterable

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.storefinders.woosmap import WoosmapSpider

# Dutch is the local language in Flanders, French in Wallonia and in majority
# French-speaking Brussels. Where the two differ, both are kept as extras.
DUTCH_REGIONS = {"Antwerpen", "Limburg", "Oost-Vlaanderen", "Vlaams-Brabant", "West-Vlaanderen"}

# The two language versions of the site use unrelated paths for a service centre.
SERVICE_CENTRE_URLS = {
    "nl": "https://www.carglass.be/nl/service-centers/",
    "fr": "https://www.carglass.be/fr/centre-de-services/",
}


class CarglassBESpider(WoosmapSpider):
    name = "carglass_be"
    item_attributes = {"brand": "Carglass", "brand_wikidata": "Q1035997"}
    key = "woos-b72b7afb-14df-3983-91c8-55d890e7fc84"
    origin = "https://www.carglass.be"
    # A single national call centre number is supplied for every location.
    drop_attributes = {"phone"}

    def parse_item(self, item: Feature, feature: dict) -> Iterable[Feature]:
        localised = feature["properties"]["user_properties"]
        language = "nl" if localised["region"] in DUTCH_REGIONS else "fr"

        branch = {code: self.strip_brand(value) for code, value in localised["localizedBranchName"].items()}
        website = {code: SERVICE_CENTRE_URLS[code] + value for code, value in localised["ewpFrontEnd"].items()}

        # The feed's name repeats the brand and is Dutch nationwide; drop it so the
        # NSI match supplies a plain "Carglass" and branch carries the local name.
        item.pop("name", None)
        item["branch"] = branch[language]
        item["city"] = localised["localizedCity"][language]
        item["street_address"] = localised["localizedAddress"][language]
        item["website"] = website[language]

        for code in ("nl", "fr"):
            item["extras"][f"website:{code}"] = website[code]
            # A translation is only worth recording where it differs from the local name.
            if branch["nl"] != branch["fr"]:
                item["extras"][f"branch:{code}"] = branch[code]
            if localised["localizedCity"]["nl"] != localised["localizedCity"]["fr"]:
                item["extras"][f"addr:city:{code}"] = localised["localizedCity"][code]
            if localised["localizedAddress"]["nl"] != localised["localizedAddress"]["fr"]:
                item["extras"][f"addr:street_address:{code}"] = localised["localizedAddress"][code]

        apply_category(Categories.SHOP_CAR_REPAIR, item)
        apply_yes_no(Extras.VEHICLE_WINDSCREEN_REPLACEMENT_SERVICES, item, True)

        yield item

    @staticmethod
    def strip_brand(name: str) -> str:
        return re.sub(r"<[^>]+>", "", name).removeprefix("Carglass® ")
