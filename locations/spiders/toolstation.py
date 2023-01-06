import json
import re

import scrapy

from locations.dict_parser import DictParser


class ToolstationSpider(scrapy.spiders.SitemapSpider):
    name = "toolstation"
    item_attributes = {"brand": "Toolstation", "brand_wikidata": "Q7824103"}
    download_delay = 1.0
    sitemap_urls = [
        "https://www.toolstation.com/sitemap/branches.xml",
        "https://www.toolstation.fr/sitemap/branches.xml",
        "https://www.toolstation.nl/sitemap/branches.xml",
    ]

    def parse(self, response):
        pattern = re.compile(r"var store = (.*?)\n", re.MULTILINE | re.DOTALL)
        store = json.loads(response.xpath('//script[contains(., "var store")]/text()').re(pattern)[0])[0]
        item = DictParser.parse(store)
        item["website"] = response.url
        item["addr_full"] = store["address_text"].split("<br /><br />")[0]
        yield item
