import json
import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class Take5USSpider(SitemapSpider, StructuredDataSpider):
    name = "take_5_us"
    item_attributes = {"brand": "Take 5", "brand_wikidata": "Q112359190"}
    sitemap_urls = [
        "https://www.take5.com/sitemap/en.xml",
        "https://www.take5carwashes.com/sitemap.xml",
    ]
    sitemap_rules = [(r"/locations/[a-z-]+/[a-z0-9-]+/\d+/?$", "parse_sd")]
    wanted_types = ["AutoRepair", "AutoWash"]
    search_for_facebook = False
    search_for_twitter = False
    search_for_image = False

    def post_process_item(self, item, response, ld_data):
        if ld_data["@type"] == "AutoWash":
            apply_category(Categories.CAR_WASH, item)
            item.pop("phone", None)
            item["opening_hours"] = self.parse_carwash_hours(response)
        else:
            item["ref"] = item.pop("name").removeprefix("Take 5 #")
            apply_category(Categories.SHOP_CAR_REPAIR, item)
            item["opening_hours"] = self.parse_repair_hours(response)
        yield item

    @staticmethod
    def parse_repair_hours(response):
        oh = OpeningHours()
        if m := re.search(r'hours\\":(\[\{\\"day.*?\])', response.text):
            for rule in json.loads(m.group(1).replace('\\"', '"')):
                if rule["is_open"]:
                    oh.add_range(rule["day"], rule["open"], rule["close"], "%I:%M %p")
                else:
                    oh.set_closed(rule["day"])
        return oh

    @staticmethod
    def parse_carwash_hours(response):
        oh = OpeningHours()
        if m := re.search(r'hours\\":(\{.*?\}\})', response.text):
            for day, rule in json.loads(m.group(1).replace('\\"', '"')).items():
                if rule["isOpen"]:
                    oh.add_range(day, rule["open"], rule["close"])
                else:
                    oh.set_closed(day)
        return oh
