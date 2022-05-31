# -*- coding: utf-8 -*-
import scrapy
import json
import re
from locations.brands import Brand
from locations.seo import extract_details


class SportsDirectSpider(scrapy.spiders.SitemapSpider):
    name = "sports_direct"
    brand = Brand.from_wikidata("Sports Direct", "Q7579661")
    download_delay = 1.0
    allowed_domains = ["www.sportsdirect.com"]
    sitemap_urls = ["https://www.sportsdirect.com/sitemap-store-pages.xml"]
    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
    }

    def parse(self, response):
        pattern = re.compile(r"var store = (.*?);\r\n", re.DOTALL)
        matches = pattern.search(response.text)
        if matches:
            store = json.loads(matches.group(1))
            item = self.brand.item(response)
            extract_details(item, store)
            item["street_address"] = store["address"]
            yield item
