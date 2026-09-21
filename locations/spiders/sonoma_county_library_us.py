from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider

# The administration building, which also hosts the "Library To Go" desk of
# whichever branch is closed for building work.
HEADQUARTERS_HOUSENUMBER = "6135"
HEADQUARTERS_STREET = "State Farm"


class SonomaCountyLibraryUSSpider(BiblioCommonsSpider):
    name = "sonoma_county_library_us"
    item_attributes = {"operator": "Sonoma County Library", "operator_wikidata": "Q21625840"}
    library_id = "sonoma"
    # Every location lists the system-wide Ask a Librarian address.
    drop_attributes = {"email"}

    def pre_process_data(self, location: dict, **kwargs) -> None:
        # e.g. number "14107", street "14107 Armstrong Woods Rd."
        address = location.get("address") or {}
        if (number := address.get("number")) and (street := address.get("street")):
            address["street"] = street.removeprefix(number).strip()

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        address = location.get("address") or {}
        if address.get("number") == HEADQUARTERS_HOUSENUMBER and (address.get("street") or "").startswith(
            HEADQUARTERS_STREET
        ):
            # The headquarters itself is closed to the public. A branch given
            # this address is closed for building work and served from the
            # headquarters lobby instead, e.g. Rohnert Park Cotati Regional
            # Library from September 2026, so its own address and hours are
            # not published. It returns once the API has them again.
            return
        apply_category(Categories.LIBRARY, item)
        yield item
