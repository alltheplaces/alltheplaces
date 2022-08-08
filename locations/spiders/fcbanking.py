# -*- coding: utf-8 -*-
import json
import re

from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser
from locations.items import GeojsonPointItem


class FcBankingSpider(SitemapSpider):
    name = "fcbanking"
    item_attributes = {"brand": "First Commonwealth Bank", "brand_wikidata": "Q5452773"}
    allowed_domains = ["www.fcbanking.com"]
    sitemap_urls = ["https://www.fcbanking.com/robots.txt"]
    sitemap_follow = ["branch-locations"]
    sitemap_rules = [(r"branch-locations/.", "parse")]

    def parse(self, response):
        map_script = response.xpath('//script/text()[contains(., "setLat")]').get()
        map_script = map_script.replace("\r", "\n")
        lat = re.search(r'setLat\("(.*)"\)', map_script)[1]
        lon = re.search(r'setLon\("(.*)"\)', map_script)[1]

        ldjson = response.xpath('//script[@type="application/ld+json"]/text()').get()
        ldjson = ldjson.replace("\r", "\n")
        data = json.loads(re.sub(r"^//.*$", "", ldjson, flags=re.M))
        item = LinkedDataParser.parse_ld(data)
        item["lat"] = lat
        item["lon"] = lon
        item["ref"] = item["website"] = response.url
        item["opening_hours"] = "; ".join(data["openingHours"])
        yield item
