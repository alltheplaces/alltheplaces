import html

from scrapy import Selector

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class BuceesUSSpider(WPStoreLocatorSpider):
    name = "bucees_us"
    item_attributes = {"brand": "Buc-ee's", "brand_wikidata": "Q4982335"}
    allowed_domains = ["buc-ees.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse_item(self, item: Feature, location: dict, **kwargs):
        item["branch"] = html.unescape(item.pop("name"))

        apply_category(Categories.FUEL_STATION, item)
        apply_yes_no(Fuel.DIESEL, item, True)
        apply_yes_no("car_wash", item, "carwash" in location["terms"])

        apply_yes_no(Fuel.OCTANE_87, item, "87" in location["octane_level"])
        apply_yes_no(Fuel.OCTANE_90, item, "90" in location["octane_level"])
        apply_yes_no(Fuel.OCTANE_92, item, "92" in location["octane_level"])
        apply_yes_no(Fuel.OCTANE_93, item, "93" in location["octane_level"])

        apply_yes_no(Fuel.ADBLUE, item, "def-at-pump" in location["terms"])
        apply_yes_no("fuel:ethanol_free", item, "ethanol-free" in location["terms"])

        yield item

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
