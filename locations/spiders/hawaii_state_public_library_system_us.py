import re
from typing import Any, Iterable

from scrapy.http import Request, Response, TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.storefinders.the_events_calendar import TheEventsCalendarSpider

TIME_RANGE_REGEX = re.compile(r"(\d{1,2}:\d{2}\s*[AP]M)\s*-\s*(\d{1,2}:\d{2}\s*[AP]M)", re.IGNORECASE)


class HawaiiStatePublicLibrarySystemUSSpider(TheEventsCalendarSpider):
    name = "hawaii_state_public_library_system_us"
    item_attributes = {"operator": "Hawaii State Public Library System", "operator_wikidata": "Q5684409"}
    events_calendar_host = "www.librarieshawaii.org"

    def post_process_item(
        self, item: Feature, response: TextResponse, venue: dict, **kwargs
    ) -> Iterable[Feature | Request]:
        # Bookmobile stops, e.g. "Maui Bookmobile – Nāpili Park".
        if "Bookmobile" in item["name"]:
            return
        # Venues are named "<Island> – <Branch>", e.g. "O‘ahu – Kapolei".
        item["branch"] = item["name"].split(" – ", 1)[-1]
        # The Library for the Blind and Print Disabled has its postcode in
        # its phone field.
        if len(re.sub(r"\D", "", item.get("phone") or "")) < 10:
            item["phone"] = None
        apply_category(Categories.LIBRARY, item)
        # The branch page has the library's name as signed, e.g. "Kapolei
        # Public Library", and its opening hours.
        yield Request(item["website"], callback=self.parse_branch_page, cb_kwargs={"item": item})

    def parse_branch_page(self, response: Response, item: Feature, **kwargs: Any) -> Iterable[Feature]:
        if name := self.clean(response.xpath('//meta[@property="og:title"]/@content').get()):
            item["name"] = name
        if item["branch"] == item["name"]:
            # e.g. "Hawai‘i State Library"
            del item["branch"]

        item["opening_hours"] = OpeningHours()
        for row in response.xpath('//table[.//*[normalize-space()="Monday"]]//tr[td]'):
            day = row.xpath("normalize-space(./td[1])").get()
            # e.g. "9:00 AM - 4:00 PM", "9:00AM-12:00PM & 1:00PM-4:00PM -",
            # "CLOSED - CLOSED" or "CLOSED -"
            times = row.xpath("normalize-space(./td[2])").get()
            if "CLOSED" in times.upper():
                item["opening_hours"].set_closed(day)
                continue
            for open_time, close_time in TIME_RANGE_REGEX.findall(times):
                item["opening_hours"].add_range(
                    day, open_time.replace(" ", ""), close_time.replace(" ", ""), time_format="%I:%M%p"
                )
        yield item
