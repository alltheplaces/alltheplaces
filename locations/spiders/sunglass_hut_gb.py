import re

from scrapy.http import JsonRequest
from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider
from locations.spiders.sunglass_hut import SUNGLASS_HUT_SHARED_ATTRIBUTES


class SunglassHutGBSpider(SitemapSpider,StructuredDataSpider):
    name = "sunglass_hut_gb"
    item_attributes = SUNGLASS_HUT_SHARED_ATTRIBUTES
    sitemap_urls = ["https://stores.sunglasshut.com/sitemap1.xml"]
    sitemap_rules = [
        (r"^https://stores.sunglasshut.com/gb/.*$", "parse_sd"),
    ]

    def post_process_item(self, item, response, location):
        if m := re.search(r'"geocodedCoordinate":{"latitude":(-?\d+\.\d+),"longitude":(-?\d+\.\d+)}', response.text):
            item["lat"], item["lon"] = m.groups()
        elif m := re.search(r'"yextDisplayCoordinate":{"latitude":(-?\d+\.\d+),"longitude":(-?\d+\.\d+)}', response.text):
            item["lat"], item["lon"] = m.groups()
        yield item
