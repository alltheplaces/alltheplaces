import re

from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours, day_range, sanitise_day
from locations.structured_data_spider import StructuredDataSpider


class SproutsFarmersMarketSpider(SitemapSpider, StructuredDataSpider):
    name = "sprouts_farmers_market"
    allowed_domains = ["www.sprouts.com"]
    item_attributes = {"brand": "Sprouts Farmers Market", "brand_wikidata": "Q7581369"}
    sitemap_urls = ["https://www.sprouts.com/store-sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/www.sprouts.com\/store\/\w\w\/*\/*\/", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["website"] = response.url
        item["opening_hours"] = ld_data["openingHours"].replace(",", ";")
        yield item

    def pre_process_data(self, ld_data, **kwargs):
        oh = OpeningHours()
        for days, open_time, open_time_ampm, close_time, close_time_ampm in re.findall(
            r"(\w+-\w+) (\d+:\d+)\s?(AM|am|PM|pm) (\d+:\d+)\s?(AM|am|PM|pm)",
            ld_data["openingHours"],
        ):
            start_day, end_day = days.split("-")
            start_day = sanitise_day(start_day)
            end_day = sanitise_day(end_day)
            for day in day_range(start_day, end_day):
                oh.add_range(
                    day,
                    open_time + open_time_ampm,
                    close_time + close_time_ampm,
                    time_format="%I:%M%p",
                )
        ld_data["openingHours"] = oh.as_opening_hours()
