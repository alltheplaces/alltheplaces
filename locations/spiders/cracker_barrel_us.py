import json
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class CrackerBarrelUSSpider(SitemapSpider, JSONBlobSpider):
    name = "cracker_barrel_us"
    item_attributes = {"brand": "Cracker Barrel", "brand_wikidata": "Q4492609"}
    allowed_domains = ["crackerbarrel.com"]
    sitemap_urls = ["https://www.crackerbarrel.com/robots.txt"]
    sitemap_rules = [(r"/locations/states/\w{2}/[-\w]+/\d+$", "parse")]

    def extract_json(self, response: TextResponse) -> list[dict]:
        return [
            DictParser.get_nested_key(
                json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()), "locationData"
            )
        ]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["street_address"] = item.pop("addr_full", None)
        item["branch"] = item.pop("name", "").split(",")[0].strip().title()
        item["opening_hours"] = self.parse_opening_hours(feature.get("storeHours", {}).get("business"))
        apply_category(Categories.RESTAURANT, item)
        yield item

    def parse_opening_hours(self, rules: list[dict]) -> OpeningHours:
        opening_hours = OpeningHours()
        for rule in rules:
            opening_hours.add_range(rule["startWeekday"], rule["startAt"], rule["endAt"])
        return opening_hours
