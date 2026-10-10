from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.the_events_calendar import TheEventsCalendarSpider


class SanBernardinoCountyLibraryUSSpider(TheEventsCalendarSpider):
    name = "san_bernardino_county_library_us"
    item_attributes = {"operator": "San Bernardino County Library", "operator_wikidata": "Q30268360"}
    events_calendar_host = "library.sbcounty.gov"

    def post_process_item(self, item: Feature, response: TextResponse, venue: dict, **kwargs) -> Iterable[Feature]:
        # Other venues host events, e.g. the Mentone Senior Center, which
        # shares its building with the Mentone Library.
        if "Library" not in item["name"] and "Learning Center" not in item["name"]:
            return
        if item["name"].endswith(" Branch Library"):
            item["branch"] = item["name"].removesuffix(" Branch Library")
        apply_category(Categories.LIBRARY, item)
        yield item
