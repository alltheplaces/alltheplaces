from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class HabitBurgerSpider(SitemapSpider, StructuredDataSpider):
    name = "habit_burger"
    item_attributes = {"brand": "The Habit Burger Grill", "brand_wikidata": "Q18158741"}
    allowed_domains = ["habitburger.com"]
    sitemap_urls = ["https://www.habitburger.com/locations-sitemap.xml"]
    wanted_types = ["Restaurant"]

    def post_process_item(self, item, response, ld_data):
        rules = ld_data["openingHours"][0].split()
        opening_hours = []
        for days, hours in zip(rules[::2], rules[1::2]):
            opening_hours.extend(f"{day} {hours}" for day in days.split(","))
        oh = OpeningHours()
        oh.from_linked_data({"openingHours": opening_hours}, "%I:%M%p")
        item["opening_hours"] = oh.as_opening_hours()

        yield item
