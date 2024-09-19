from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser
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
        item["opening_hours"] = LinkedDataParser.parse_opening_hours({"openingHours": opening_hours}, "%I:%M%p")

        yield item
