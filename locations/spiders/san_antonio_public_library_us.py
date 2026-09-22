import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider

# A branch closed for renovation is renamed after its off-site interim
# service point, e.g. "Denver Heights (Carver Interim Location)", but keeps
# the branch's own address and coordinates.
INTERIM_NAME_REGEX = re.compile(r".+\((.+) Interim Location\)")


class SanAntonioPublicLibraryUSSpider(BiblioCommonsSpider):
    name = "san_antonio_public_library_us"
    item_attributes = {"operator": "San Antonio Public Library", "operator_wikidata": "Q5642025"}
    library_id = "mysapl"

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        if location.get("id") == "TEXANA":
            # The Texana/Genealogy department on the 6th floor of the Central Library.
            return

        name = item.pop("name") or ""
        if m := INTERIM_NAME_REGEX.fullmatch(name):
            name = "{} Library".format(m.group(1))
            if not item.get("opening_hours"):
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].set_closed(DAYS_FULL)
        item["name"] = "San Antonio Central Library" if name == "Central Library" else name
        if name.endswith(" Library Portal"):
            # A small library space inside the Briscoe Western Art Museum.
            item["located_in"] = "Briscoe Western Art Museum"
            item["located_in_wikidata"] = "Q18343189"

        apply_category(Categories.LIBRARY, item)

        yield item
