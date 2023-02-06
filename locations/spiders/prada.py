import re

from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class PradaSpider(SitemapSpider, StructuredDataSpider):
    name = "prada"
    item_attributes = {"brand": "Prada", "brand_wikidata": ""}
    sitemap_urls = ["https://www.prada.com/us/en/sitemap.xml"]
    sitemap_rules = [("/store-locator/", "parse_sd")]

    def pre_process_data(self, ld_data, **kwargs):
        oh = OpeningHours()
        for day, start_time, end_time in re.findall(
            r"(\w+) (\d\d:\d\d (?:am|pm)) - (\d\d:\d\d (?:am|pm))", ld_data["openingHours"]
        ):
            oh.add_range(day, start_time, end_time, time_format="%I:%M %p")

        ld_data["openingHours"] = oh.as_opening_hours()
