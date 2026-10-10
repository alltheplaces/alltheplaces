from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.the_events_calendar import TheEventsCalendarSpider


class BullittCountyPublicLibraryUSSpider(TheEventsCalendarSpider):
    name = "bullitt_county_public_library_us"
    item_attributes = {"operator": "Bullitt County Public Library", "operator_wikidata": "Q69476748"}
    events_calendar_host = "bcplib.org"

    def post_process_item(self, item: Feature, response: TextResponse, venue: dict, **kwargs) -> Iterable[Feature]:
        # "Central Library" and "<Town> Branch"; other venues are event
        # spaces, such as the Dorothea Stottman Annex.
        if item["name"] == "Central Library":
            item["branch"] = item["name"]
            item["name"] = self.item_attributes["operator"]
        elif item["name"].endswith(" Branch"):
            item["branch"] = item["name"].removesuffix(" Branch")
            item["name"] = "{} Library".format(item["name"])
        else:
            return
        apply_category(Categories.LIBRARY, item)
        yield item
