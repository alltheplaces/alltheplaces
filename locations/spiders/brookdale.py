# -*- coding: utf-8 -*-
from pathlib import Path
import urllib.parse
import scrapy

from locations.linked_data_parser import LinkedDataParser


class BrookdaleSpider(scrapy.spiders.SitemapSpider):
    name = "brookdale"
    item_attributes = {"brand": "Brookdale"}
    allowed_domains = ["www.brookdale.com"]
    sitemap_urls = [
        "https://www.brookdale.com/robots.txt",
    ]
    sitemap_rules = [
        (r"/communities/[^/]+$", "parse"),
    ]

    def parse(self, response):
        if response.request.meta.get("redirect_reasons") == [301]:
            # Returning 301 when should be 404
            return
        item = LinkedDataParser.parse(response, "Residence")
        path = urllib.parse.urlsplit(response.url).path
        item["ref"] = Path(path).stem.removeprefix("brookdale-")
        yield item
