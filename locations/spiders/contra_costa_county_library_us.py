import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider

# A branch closed for a renovation or other long closure keeps its regular
# hours, with a note such as "Kensington Library is closed for remodel
# starting July 24, 2026 until estimated February 2028. Book drops closed."
# Shorter changes (e.g. "closed on Mondays") don't close the book drop.
BOOK_DROP_CLOSED_REGEX = re.compile(r"\bbook drops?(?: is| are)? closed\b", re.IGNORECASE)


class ContraCostaCountyLibraryUSSpider(BiblioCommonsSpider):
    name = "contra_costa_county_library_us"
    item_attributes = {"operator": "Contra Costa County Library", "operator_wikidata": "Q5165604"}
    library_id = "ccclib"

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        branch = item.pop("name")
        if branch.startswith("Juvenile Hall"):
            # "Juvenile Hall - Staff Use Only", closed to the public.
            return

        item["branch"] = branch
        item["name"] = "{} Library".format(branch)

        if BOOK_DROP_CLOSED_REGEX.search(location.get("hoursNote") or ""):
            oh = OpeningHours()
            oh.set_closed(DAYS_FULL)
            item["opening_hours"] = oh

        apply_category(Categories.LIBRARY, item)

        yield item
