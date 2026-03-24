import json
import re

from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class SafewayCASpider(SitemapSpider):
    name = "safeway_ca"
    item_attributes = {"brand": "Safeway", "brand_wikidata": "Q17111901"}
    sitemap_urls = ("https://www.safeway.ca/sitemap/stores/sitemap.xml",)
    sitemap_rules = [("/stores/", "parse")]

    def parse(self, response):
        raw_data = response.xpath('//*[contains(text(),"application/ld+json")]/text()').get().replace("\\", "")
        if data := re.search(r"__html\":\"({.*})\"", raw_data):
            store_data = json.loads(data.group(1))
            item = DictParser.parse(store_data)
            item["website"] = item["ref"] = response.url
            item["lat"], item["lon"] = re.search(r"lat\":(-?\d+\.\d+),\"lng\":(-?\d+\.\d+)", raw_data).groups()
            item["opening_hours"] = OpeningHours()
            for day_time in store_data["openingHours"]:
                item["opening_hours"].add_ranges_from_string(day_time)
            yield item
