# -*- coding: utf-8 -*-
import urllib.parse

import scrapy
from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem

BRANDS = {
    "locations.carlsjr.com": {"brand": "Carl's Jr.", "brand_wikidata": "Q1043486"},
    "locations.hardees.com": {"brand": "Hardee's", "brand_wikidata": "Q1585088"},
}


class HardeesCarlsJrSpider(SitemapSpider):
    name = "hardees_carlsjr"
    allowed_domains = ["locations.hardees.com", "locations.carlsjr.com"]
    sitemap_urls = [
        "https://locations.hardees.com/robots.txt",
        "https://locations.carlsjr.com/robots.txt",
    ]
    sitemap_rules = [(r"https://locations\..*\.com/.*/.*/.*", "parse")]

    def parse(self, response):
        hours = OpeningHours()
        for row in response.xpath('//*[@itemprop="openingHours"]/@content').extract():
            day, interval = row.split(" ", 1)
            if interval == "All Day":
                interval = "00:00-00:00"
            elif interval == "Closed":
                continue
            open_time, close_time = interval.split("-")
            hours.add_range(day, open_time, close_time)
        properties = {
            "ref": response.css("main").attrib["itemid"],
            "website": response.url,
            "lat": response.css('[itemprop="latitude"]').attrib["content"],
            "lon": response.css('[itemprop="longitude"]').attrib["content"],
            "name": response.xpath("//title/text()").get().split(":")[0],
            "street_address": response.css('[itemprop="streetAddress"]').attrib[
                "content"
            ],
            "city": response.css(".Address-city::text").get(),
            "state": response.css('[itemprop="addressRegion"]::text').get(),
            "postcode": response.css('[itemprop="postalCode"]::text').get(),
            "phone": response.css('[itemprop="telephone"]::text').get(),
            "opening_hours": hours.as_opening_hours(),
        }
        hostname = urllib.parse.urlparse(response.url).hostname
        properties.update(BRANDS[hostname])
        return GeojsonPointItem(**properties)
