# -*- coding: utf-8 -*-
import re

from locations.linked_data_parser import LinkedDataParser
from scrapy.spiders import SitemapSpider


class WyndhamSpider(SitemapSpider):
    name = "wyndham"
    download_delay = 1
    allowed_domains = ["www.wyndhamhotels.com"]
    sitemap_urls = ["https://www.wyndhamhotels.com/sitemap.xml"]
    sitemap_follow = [
        r"https:\/\/www\.wyndhamhotels\.com\/sitemap_en-us_([\w]{2})_properties_\d\.xml"
    ]
    sitemap_rules = [
        (
            r"https:\/\/www\.wyndhamhotels\.com\/([-\w]+)\/([-\w]+)\/([-\w]+)\/overview",
            "parse_property",
        )
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse_property(self, response):
        item = LinkedDataParser.parse(response, "Hotel")

        item["ref"] = response.url.replace(
            "https://www.wyndhamhotels.com/", ""
        ).replace("/overview", "")

        item["brand"] = re.match(self.sitemap_rules[0][0], response.url).group(1)

        return item
