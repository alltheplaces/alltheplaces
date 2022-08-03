# -*- coding: utf-8 -*-
import json

import scrapy
from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser


class Take5OilChangeSpider(SitemapSpider):
    name = "take5"
    item_attributes = {
        "brand": "Take 5 Oil Change",
        "brand_wikidata": "Q112359190",
    }
    allowed_domains = ["www.take5oilchange.com"]
    sitemap_urls = ["https://www.take5oilchange.com/robots.txt"]
    sitemap_rules = [
        (r"www\.take5oilchange\.com/locations/.*/.*/", "parse"),
    ]

    def parse(self, response):
        locations = response.xpath('//div[@id="data-json-locations"]/@data-json').get()
        if locations is not None:
            for row in json.loads(locations):
                yield scrapy.Request(
                    f'https://www.take5oilchange.com/locations/{row["storeUrl"]}'
                )

        ld = LinkedDataParser.find_linked_data(response, "Service")
        if ld is not None:
            item = LinkedDataParser.parse_ld(ld["provider"])
            item["ref"] = response.xpath("//@data-storeid").get()
            yield item
