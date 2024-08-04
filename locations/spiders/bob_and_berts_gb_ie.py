from scrapy import Selector

from locations.hours import OpeningHours, sanitise_day
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class BobAndBertsGBIESpider(WPStoreLocatorSpider):
    name = "bob_and_berts_gb_ie"
    item_attributes = {
        "brand_wikidata": "Q113494662",
        "brand": "Bob & Berts",
    }
    allowed_domains = [
        "bobandberts.co.uk",
    ]

    # TODO: This is a copy/paste from BuceesUSSpider. Is it worth refactoring to a generalised hours-in-html method?
    def parse_opening_hours(self, location: dict, days: dict, **kwargs) -> OpeningHours:
        sel = Selector(text=location["hours"])
        oh = OpeningHours()
        for rule in sel.xpath("//tr"):
            day = sanitise_day(rule.xpath("./td/text()").get())
            times = rule.xpath("./td/time/text()").get()
            if not day or not times:
                continue
            if times.lower() in ["closed"]:
                continue
            start_time, end_time = times.split("-")
            oh.add_range(
                day,
                start_time.strip(),
                end_time.strip(),
                time_format="%I:%M %p" if ("AM" in start_time) else "%H:%M",
            )

        return oh
