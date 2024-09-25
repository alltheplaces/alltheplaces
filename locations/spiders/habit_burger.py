from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class HabitBurgerSpider(SitemapSpider, StructuredDataSpider):
    name = "habit_burger"
    item_attributes = {"brand": "The Habit Burger Grill", "brand_wikidata": "Q18158741"}
    allowed_domains = ["habitburger.com"]
    sitemap_urls = ["https://www.habitburger.com/locations-sitemap.xml"]
    wanted_types = ["Restaurant"]
    time_format = "%I:%M%p"

    def pre_process_data(self, ld_data: dict, **kwargs):
        rules = ld_data["openingHours"][0].split()
        opening_hours = []
        for days, hours in zip(rules[::2], rules[1::2]):
            opening_hours.extend(f"{day} {hours}" for day in days.split(","))
        ld_data["openingHours"] = opening_hours

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["name"] = None
        item["branch"] = response.xpath('//h1[@class="loc_title bebas"]/text()').get()
        yield item
