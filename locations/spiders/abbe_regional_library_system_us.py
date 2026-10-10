import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class AbbeRegionalLibrarySystemUSSpider(Spider):
    name = "abbe_regional_library_system_us"
    item_attributes = {"operator": "ABBE Regional Library System", "operator_wikidata": "Q69490330"}
    # The system's LibCal tenant (abbe-lib.libcal.com, iid 6967) has hours
    # only, and those for the Nancy Carson Library are wrong, so the branch
    # pages of the library's own site are used instead.
    start_urls = ["https://www.abbe-lib.org/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable:
        yield from response.follow_all(css=".post__title-link", callback=self.parse_branch)

    def parse_branch(self, response: Response) -> Iterable[Feature]:
        address = [line.strip() for line in response.css(".post__addressmap-address::text").getall() if line.strip()]
        if not address:
            # The outreach van, which has no address.
            return
        item = Feature()
        item["ref"] = response.css("article.lsvr_listing").re_first(r"\bpost-(\d+)\b")
        item["website"] = response.url

        title = response.css("h1.post__title::text").get().strip()
        if m := re.fullmatch(r"(.+) \((.+)\)", title):
            # e.g. "Nancy Carson Library (North Augusta)"
            item["name"], item["branch"] = m.groups()
        else:
            item["name"] = title
            if m := re.fullmatch(r"(.+) Branch Library", title):
                item["branch"] = m.group(1)

        if m := re.fullmatch(r"(.+), ([A-Z]{2}) (\d{5})", address[-1]):
            item["street_address"] = ", ".join(address[:-1])
            item["city"], item["state"], item["postcode"] = m.groups()
        else:
            item["addr_full"] = ", ".join(address)
        item["phone"] = response.css('.post__contact-item--phone a[href^="tel:"]::text').get()
        if latlong := response.css("[data-latlong]::attr(data-latlong)").get():
            item["lat"], item["lon"] = latlong.split(",")

        item["opening_hours"] = OpeningHours()
        for day in response.css(".post__hours-item"):
            day_name = day.css(".post__hours-item-day::text").get().strip()
            ranges = day.css(".post__hours-item-value-from-to")
            if not ranges:
                if "Closed" in day.css(".post__hours-item-value::text").get(""):
                    item["opening_hours"].set_closed(day_name)
                continue
            for hours in ranges:
                item["opening_hours"].add_range(
                    day_name,
                    hours.css(".post__hours-item-value-from::text").get().strip(),
                    hours.css(".post__hours-item-value-to::text").get().strip(),
                    time_format="%I:%M %p",
                )

        apply_category(Categories.LIBRARY, item)
        yield item
