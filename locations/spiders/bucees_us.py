import html

import scrapy

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class BuceesUSSpider(scrapy.Spider):
    name = "bucees_us"
    item_attributes = {"brand": "Buc-ee's", "brand_wikidata": "Q4982335"}
    start_urls = ["https://buc-ees.com/wp-admin/admin-ajax.php?action=store_search&autoload=1"]

    def parse(self, response, **kwargs):
        for store in response.json():
            store["street_address"] = ", ".join(filter(None, [store.pop("address"), store.pop("address2")]))
            item = DictParser.parse(store)
            item["name"] = html.unescape(store["store"])
            item["opening_hours"] = OpeningHours()

            hours_table = scrapy.Selector(text=store["hours"])
            days = hours_table.css("td:first-child::text").getall()
            hours = hours_table.css("td:last-child::text, td:last-child time::text").getall()

            for day, day_hours in zip(days, hours):
                if "Closed" in day_hours:
                    continue

                open_time, close_time = day_hours.split(" - ")
                item["opening_hours"].add_range(
                    day=day,
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%I:%M %p" if ("AM" in open_time) else "%H:%M",
                )

            apply_category(Categories.FUEL_STATION, item)
            apply_yes_no(Fuel.DIESEL, item, True)
            apply_yes_no("car_wash", item, "carwash" in store["terms"])

            apply_yes_no(Fuel.OCTANE_87, item, "87" in store["octane_level"])
            apply_yes_no(Fuel.OCTANE_90, item, "90" in store["octane_level"])
            apply_yes_no(Fuel.OCTANE_92, item, "92" in store["octane_level"])
            apply_yes_no(Fuel.OCTANE_93, item, "93" in store["octane_level"])

            apply_yes_no(Fuel.ADBLUE, item, "def-at-pump" in store["terms"])
            apply_yes_no("fuel:ethanol_free", item, "ethanol-free" in store["terms"])

            yield item
