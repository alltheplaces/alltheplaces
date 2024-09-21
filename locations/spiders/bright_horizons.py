import logging
import re
import time

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class BrightHorizonsSpider(SitemapSpider, StructuredDataSpider):
    name = "bright_horizons"
    item_attributes = {
        "brand": "Bright Horizons",
        "brand_wikidata": "Q4967421",
        "country": "US",
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
        oh = ld_data["openingHours"]
        if oh != "Not Available":
            days, times = oh.split(": ")

            if days != "M-F":
                logging.error("Unexpected days: " + days)
            else:
                start_time, end_time = times.replace("a.m.", "AM").replace("p.m.", "PM").split(" to ")

                start_time = time.strftime("%H:%M", time.strptime(start_time, "%I:%M %p"))
                end_time = time.strftime("%H:%M", time.strptime(end_time, "%I:%M %p"))

                item["opening_hours"] = f"Mo-Fr {start_time}-{end_time}"

            yield item
