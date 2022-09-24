# -*- coding: utf-8 -*-
from scrapy.spiders import SitemapSpider
from locations.structured_data_spider import StructuredDataSpider
import json


class ReiSpider(SitemapSpider, StructuredDataSpider):
    name = "rei"
    item_attributes = {"brand": "REI", "brand_wikidata": "Q3414933", "country": "US"}
    allowed_domains = ["www.rei.com"]
    sitemap_urls = ["https://www.rei.com/sitemap-stores.xml"]
    sitemap_rules = [(r"^https://www.rei.com/stores/[^/]+$", "parse_sd")]
    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (X11; Linux x86_64; rv:99.0) Gecko/20100101 Firefox/99.0"
    }
    download_delay = 2.5
    wanted_types = ["Store"]

    def inspect_item(self, item, response):
        hours = json.loads(
            response.xpath('//script[@id="store-schema"]/text()').extract_first()
        )["openingHours"]
        for i, h in enumerate(hours):
            hours[i] = (
                h.replace("Mon", "Mo")
                .replace("Tue", "Tu")
                .replace("Wed", "We")
                .replace("Thu", "Th")
                .replace("Fri", "Fr")
                .replace("Sat", "Sa")
                .replace("Sun", "Su")
                .replace(" - ", "-")
            )
        item["opening_hours"] = "; ".join(hours)
        yield item
