from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider


class StarkCountyDistrictLibraryUSSpider(BiblioCommonsSpider):
    name = "stark_county_district_library_us"
    item_attributes = {"operator": "Stark County District Library", "operator_wikidata": "Q69487363"}
    library_id = "starklibrary"

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        if street := item.get("street"):
            # e.g. "Cleveland Ave. SW (inside of shopping plaza)"
            item["street"] = street.split(" (", 1)[0]

        if location.get("id") == "LP":
            # "24/7 Library - Pike Township", a stand-alone holds locker and
            # book drop listing the Main Library's phone number.
            item.pop("phone", None)
            apply_category(Categories.PARCEL_LOCKER, item)
            yield item
            return

        branch = item.pop("name")
        item["branch"] = branch.removesuffix(" Branch").removesuffix(" Library")
        # The Main Library is the system's headquarters and is mapped with its
        # name; the branches are e.g. "Jackson Community Branch Library".
        item["name"] = self.item_attributes["operator"] if branch == "Main Library" else "{} Library".format(branch)
        apply_category(Categories.LIBRARY, item)

        yield item
