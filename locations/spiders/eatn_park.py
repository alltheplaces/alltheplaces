import re

from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider

HOURS_RE = re.compile(r"(?P<day>\w+) (?P<open_time>\S+) - (?P<close_time>\S+)")


class EatnParkSpider(SitemapSpider, StructuredDataSpider):
    name = "eatn_park"
    item_attributes = {"brand": "Eat'n Park", "brand_wikidata": "Q5331211"}
    sitemap_urls = ["https://locations.eatnpark.com/robots.txt"]
    sitemap_rules = [("/restaurants-", "parse_sd")]

    def post_process_item(self, item, response, ld_data):
        item["name"] = response.css("span.location-name::text").get()
        item["ref"] = re.search(r"-(\d+)\.html", response.url).group(1)
        yield item
