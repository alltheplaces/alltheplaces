import json
import re

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider
from locations.hours import OpeningHours
from locations.items import Feature

HOURS_RE = re.compile(r"(?P<day>\w+) (?P<open_time>\S+) - (?P<close_time>\S+)")


class EatnParkSpider(SitemapSpider, StructuredDataSpider):
    name = "eatn_park"
    item_attributes = {"brand": "Eat'n Park", "brand_wikidata": "Q5331211"}
    sitemap_urls = ["https://locations.eatnpark.com/robots.txt"]
    sitemap_rules = [(r"/restaurants-", "parse_sd")]

    def post_process_item(self, item, response, ld_data):
        opening_hours = OpeningHours()
        for m in HOURS_RE.finditer(ld_data["openingHours"]):
            g = m.groupdict()
            opening_hours.add_range(g["day"], g["open_time"], g["close_time"])
        item["opening_hours"] = opening_hours
        item["name"] = response.css("span.location-name::text").get(),
        item["ref"] = re.search(r"-(\d+)\.html", response.url).group(1)
        yield item
