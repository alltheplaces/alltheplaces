# -*- coding: utf-8 -*-
from locations.google_url import extract_google_position
from locations.spiders.vapestore_gb import clean_address
from locations.structured_data_spider import StructuredDataSpider

from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor


class WeBuyAnyCarGB(CrawlSpider, StructuredDataSpider):
    name = "webuyanycar_gb"
    item_attributes = {
        "brand": "WeBuyAnyCar",
        "brand_wikidata": "Q7977432",
        "country": "GB",
    }
    allowed_domains = ["www.webuyanycar.com"]
    start_urls = ["https://www.webuyanycar.com/branch-locator/"]
    rules = [
        Rule(
            LinkExtractor(allow=".*/branch-locator/.*"),
            callback="parse_sd",
            follow=False,
        )
    ]
    download_delay = 0.5
    wanted_types = ["LocalBusiness"]

    def inspect_item(self, item, response):
        extract_google_position(item, response)
        item["street_address"] = clean_address(item["street_address"])
        yield item
