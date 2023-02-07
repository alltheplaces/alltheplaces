import json

import requests
from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class EdwardJonesSpider(SitemapSpider, StructuredDataSpider):
    name = "edwardjones"
    item_attributes = {"brand": "Edward Jones", "brand_wikidata": "Q5343830"}
    allowed_domains = ["www.edwardjones.com"]
    sitemap_urls = ["https://www.edwardjones.com/us-en/sitemap/financial-advisor/sitemap.xml"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        oh = OpeningHours()
        oh.from_linked_data(ld_data, time_format="%H:%M:%S")
        item["opening_hours"] = oh.as_opening_hours()
        yield item
