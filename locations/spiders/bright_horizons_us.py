import re

from scrapy.spiders import SitemapSpider

from locations.hours import DAYS_WEEKDAY, OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class BrightHorizonsUSSpider(SitemapSpider, StructuredDataSpider):
    name = "bright_horizons_us"
    item_attributes = {
        "brand": "Bright Horizons",
        "brand_wikidata": "Q4967421",
    }
    allowed_domains = ["brighthorizons.com"]
    sitemap_urls = ["https://child-care-preschool.brighthorizons.com/sitemap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/child-care-preschool\.brighthorizons\.com\/(\w{2})\/(\w+)\/([-\w]+)$",
            "parse_sd",
        )
    ]
    wanted_types = ["ChildCare"]

    def sitemap_filter(self, entries):
        for entry in entries:
            match = re.match(self.sitemap_rules[0][0], entry["loc"])
            if match:
                if match.group(1) == "ZZ":
                    # ZZ is there testing data
                    continue
                yield entry

    def post_process_item(self, item, response, ld_data):
        if opening_hours := ld_data.get("openingHours"):
            try:
                item["opening_hours"] = self.parse_opening_hours(opening_hours, response.url)
            except Exception as e:
                self.logger.warning(f"Failed to parse opening hours for {response.url}, {e}")
                self.crawler.stats.inc_value(f"atp/{self.name}/hours/failed")
        yield item

    def parse_opening_hours(self, opening_hours, url):
        o = OpeningHours()
        if opening_hours != "Not Available":
            if "M-F" in opening_hours:
                days, times = opening_hours.split(": ")
                start_time, end_time = times.replace(" a.m.", "AM").replace(" p.m.", "PM").split(" to ")
                o.add_days_range(DAYS_WEEKDAY, start_time.strip(), end_time.strip(), time_format="%I:%M%p")
        return o.as_opening_hours()
