# -*- coding: utf-8 -*-
import scrapy, json, re
from locations.brands import Brand
from locations.seo import extract_details


class ToolstationSpider(scrapy.spiders.SitemapSpider):
    name = "toolstation"
    brand = Brand.from_wikidata("Toolstation", "Q7824103")
    download_delay = 1.0
    sitemap_urls = [
        "https://www.toolstation.com/sitemap/branches.xml",
        "https://www.toolstation.fr/sitemap/branches.xml",
        "https://www.toolstation.nl/sitemap/branches.xml",
    ]

    def parse(self, response):
        pattern = re.compile(r"var store = (.*?)\n", re.MULTILINE | re.DOTALL)
        store = json.loads(
            response.xpath('//script[contains(., "var store")]/text()').re(pattern)[0]
        )[0]
        item = self.brand.item(response)
        item["addr_full"] = store["address_text"].split("<br /><br />")[0]
        yield extract_details(item, store)
