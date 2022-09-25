# -*- coding: utf-8 -*-
import re

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class CondadoTacosSpider(SitemapSpider, StructuredDataSpider):
    name = "condado_tacos"
    item_attributes = {"brand": "Condado Tacos"}
    wanted_types = ["Restaurant"]
    allowed_domains = ["locations.condadotacos.com"]
    sitemap_urls = ["https://locations.condadotacos.com/sitemap.xml"]
    sitemap_rules = [
        (r"/condado-tacos-", "parse_sd"),
    ]

    def inspect_item(self, item, response):
        description = response.css("meta[name=description]").attrib["content"]
        [name] = re.search(r"(Condado [^,]+),", description).groups()
        item["name"] = name
        item["country"] = response.css("[itemprop=addressCountry]::text").get()
        yield item
