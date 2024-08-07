from locations.storefinders.wp_store_locator import WPStoreLocatorSpider
import logging

from scrapy import Selector, Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.geo import point_locations
from locations.hours import DAYS_BY_FREQUENCY, OpeningHours, sanitise_day
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class PizzaPerfectZASpider(WPStoreLocatorSpider):
    name = "pizza_perfect_za"
    item_attributes = {
        "brand_wikidata": "Q116619227",
        "brand": "Pizza Perfect",
    }
    allowed_domains = [
        "pizzaperfect.co.za",
    ]
    max_results = 100
    search_radius = 50
    # TODO: We do not have this file yet
    # searchable_point_files = ["za_centroids_100km_radius.csv"]
    # country_filter = ["ZA"]

    def parse_opening_hours(self, location: dict, days: dict, **kwargs) -> OpeningHours:
        if not location.get("hours"):
            return
        sel = Selector(text=location["hours"])
        oh = OpeningHours()
        for rule in sel.xpath("//tr"):
            day = sanitise_day(rule.xpath("./td/text()").get(), days)
            times = rule.xpath("./td/time/text()").get()
            if not day or not times:
                continue
            if times.lower() in ["closed"]:
                continue
            start_time, end_time = times.split("-")
            # TODO: There must be a better way than this
            try:
                oh.add_range(day, start_time.strip(), end_time.strip(), time_format="%I:%M %p")
            except ValueError:
                oh.add_range(day, start_time.strip(), end_time.strip(), time_format="%H:%M %p")

        return oh
