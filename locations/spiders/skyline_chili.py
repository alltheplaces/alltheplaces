import json

from scrapy.spiders import SitemapSpider

from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class SkylineChiliSpider(SitemapSpider, StructuredDataSpider):
    name = "skyline_chili"
    item_attributes = {
        "name": "Skyline Chili",
        "brand": "Skyline Chili",
        "brand_wikidata": "Q151224",
    }

    sitemap_urls = ["https://locations.skylinechili.com/sitemap.xml"]

    def post_process_item(self, item, response, ld_data):
        item['opening_hours'] = self.parse_hours(ld_data['openingHoursSpecification'])
        yield item

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        for spec in hours:
            if {"dayOfWeek", "closes", "opens"} <= spec.keys():
                opening_hours.add_range(spec["dayOfWeek"][:2], spec["opens"], spec["closes"])
            elif {"opens", "closes"} <= spec.keys():
                for day in DAYS:
                    opening_hours.add_range(day, spec["opens"], spec["closes"])
            else:
                continue
        return opening_hours.as_opening_hours()