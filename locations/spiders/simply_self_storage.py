import re

import scrapy

from locations.hours import OpeningHours
from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser


class SimplySelfStorageSpider(scrapy.spiders.SitemapSpider):
    name = "simply_self_storage"
    item_attributes = {"brand": "Simply Self Storage"}
    allowed_domains = ["simplyss.com"]
    sitemap_urls = ["https://www.simplyss.com/robots.txt"]

    sitemap_rules = [
        (r"-self-storage/$", "parse"),
    ]

    def parse(self, response):
        item = LinkedDataParser.parse(response, "SelfStorage")
        item["ref"] = re.search(r"location_id=(\d+)", response.text)[1]

        response.selector.root.set("itemscope")
        response.selector.root.set("itemtype", "http://schema.org/Thing")
        ld = MicrodataParser.convert_to_graph(MicrodataParser.extract_microdata(response))
        oh = OpeningHours()
        oh.from_linked_data(ld, "%I:%M %p")
        item["opening_hours"] = oh.as_opening_hours()

        if isinstance(ld["telephone"], list):
            item["phone"] = ";".join(ld["telephone"])
        else:
            item["phone"] = ld["telephone"]
        yield item
