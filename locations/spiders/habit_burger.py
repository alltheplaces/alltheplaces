import json

from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class HabitBurgerSpider(SitemapSpider, StructuredDataSpider):
    name = "habit-burger"
    allowed_domains = ["habitburger.com"]
    sitemap_urls = ["https://www.habitburger.com/locations-sitemap.xml"]
    sitemap_rules = [("", "parse_sd")]
    wanted_types = ["Restaurant"]

    def inspect_item(self, item, response):
        openingHour = json.loads(response.xpath('//*[@id="content"]/script[1]/text()').get())
        openingHour = openingHour.get("openingHours")[0].split()
        days = [openingHour[i] for i in range(0, len(openingHour), 2)]
        hours = [openingHour[i] for i in range(1, len(openingHour), 2)]
        oh = OpeningHours()
        for i in range(len(openingHour) // 2):
            for day in days[i].split(","):
                oh.add_range(
                    day=day,
                    open_time=hours[i].split("-")[0],
                    close_time=hours[i].split("-")[1],
                    time_format="%I:%M%p",
                )
        item["opening_hours"] = oh.as_opening_hours()

        yield item
