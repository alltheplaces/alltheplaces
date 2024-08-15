import json
import logging
import re
import time

from scrapy.spiders import SitemapSpider

from locations.items import Feature


class BrightHorizonsSpider(SitemapSpider):
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
            "parse_store",
        )
    ]

    def sitemap_filter(self, entries):
        for entry in entries:
            match = re.match(self.sitemap_rules[0][0], entry["loc"])
            if match:
                if match.group(1) == "ZZ":
                    # ZZ is there testing data
                    continue
                yield entry

    def parse_store(self, response):
        linked_data = response.xpath('//script[@type="application/ld+json"]/text()').getall()
        for ld in linked_data:
            item = json.loads(ld)

            if item["@type"] != "ChildCare":
                continue

            if not item.get("name"):
                continue

            properties = {
                "lat": item["geo"].get("latitude"),
                "lon": item["geo"].get("longitude"),
                "name": item["name"],
                "street_address": item["address"]["streetAddress"],
                "city": item["address"]["addressLocality"],
                "state": item["address"]["addressRegion"],
                "postcode": item["address"]["postalCode"],
                "phone": item.get("telephone"),
                "website": response.request.url,
                "ref": item["@id"],
            }

            oh = item["openingHours"]
            if oh != "Not Available":
                days, times = oh.split(": ")

                if days != "M-F":
                    logging.error("Unexpected days: " + days)
                else:
                    start_time, end_time = times.replace("a.m.", "AM").replace("p.m.", "PM").split(" to ")

                    start_time = time.strftime("%H:%M", time.strptime(start_time, "%I:%M %p"))
                    end_time = time.strftime("%H:%M", time.strptime(end_time, "%I:%M %p"))

                    properties["opening_hours"] = f"Mo-Fr {start_time}-{end_time}"

            yield Feature(**properties)
