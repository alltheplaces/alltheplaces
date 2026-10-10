from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.the_events_calendar import TheEventsCalendarSpider


class OcmulgeeRegionalLibrarySystemUSSpider(TheEventsCalendarSpider):
    name = "ocmulgee_regional_library_system_us"
    item_attributes = {"operator": "Ocmulgee Regional Library System", "operator_wikidata": "Q30634615"}
    events_calendar_host = "orls.org"

    def post_process_item(self, item: Feature, response: TextResponse, venue: dict, **kwargs) -> Iterable[Feature]:
        apply_category(Categories.LIBRARY, item)
        yield item
