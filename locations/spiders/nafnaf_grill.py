# -*- coding: utf-8 -*-
import json
import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class NafnafGrillSpider(scrapy.spiders.SitemapSpider):
    download_delay = 1
    name = "nafnaf_grill"
    item_attributes = {"brand": "Naf Naf Grill", "brand_wikidata": "Q111901442"}
    allowed_domains = ["www.nafnafgrill.com"]
    sitemap_urls = ["https://www.nafnafgrill.com/location-sitemap.xml"]
    sitemap_rules = [
        (
            r"https://www.nafnafgrill.com/locations/([\w-]+)",
            "parse_store",
        ),
    ]

    def sitemap_filter(self, entries):
        for entry in entries:
            if entry["loc"] != "https://www.nafnafgrill.com/locations/%state%/":
                yield entry

    def parse_store(self, response):
        properties = {
            "phone": response.xpath('//p[@class="uabb-infobox-title"]/text()')[1].get(),
            "addr_full": response.xpath(
                '//div[@class="fl-rich-text"]/p[2]/text()'
            ).get(),
            "ref": ld["@id"],
            "website": ld["url"],
            "lat": ld["geo"]["latitude"],
            "lon": ld["geo"]["longitude"],
            "name": ld["name"],
        }

        oh = OpeningHours()
        for rule in ld["openingHoursSpecification"]:
            for day in rule["dayOfWeek"]:
                oh.add_range(day[:2], rule["opens"], rule["closes"])

        properties["opening_hours"] = oh.as_opening_hours()

        yield GeojsonPointItem(**properties)
