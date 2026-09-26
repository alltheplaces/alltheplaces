from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.the_events_calendar import TheEventsCalendarSpider


class TrailsRegionalLibraryUSSpider(TheEventsCalendarSpider):
    name = "trails_regional_library_us"
    item_attributes = {"operator": "Trails Regional Library", "operator_wikidata": "Q69481162"}
    events_calendar_host = "www.trailslibrary.org"

    def post_process_item(self, item: Feature, response: TextResponse, venue: dict, **kwargs) -> Iterable[Feature]:
        # e.g. "Odessa Branch"; other venues host events, such as the
        # Concordia Community Center.
        if not item["name"].endswith(" Branch"):
            return
        item["branch"] = item["name"].removesuffix(" Branch")
        item["name"] = "{} Branch Library".format(item["branch"])
        apply_category(Categories.LIBRARY, item)
        yield item
