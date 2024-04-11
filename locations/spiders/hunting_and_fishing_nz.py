import json

from chompjs import parse_js_object
from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class HuntingAndFishingNZSpider(Spider):
    name = "hunting_and_fishing_nz"
    item_attributes = {"brand": "Hunting & Fishing New Zealand", "brand_wikidata": "Q124062188"}
    allowed_domains = ["www.huntingandfishing.co.nz"]
    start_urls = ["https://www.huntingandfishing.co.nz/store-locator"]

    def parse(self, response):
        stores_js = (
            "[{"
            + response.xpath("//script[contains(text(), '\"sources\": [{')]/text()")
            .get()
            .split('"sources": [{', 1)[1]
            .split("}]", 1)[0]
            + "}]"
        )
        locations = parse_js_object(stores_js)
        for location in locations:
            item = DictParser.parse(location)
            item.pop("state", None)
            item.pop("street", None)
            item["ref"] = location["source_code"]
            item["street_address"] = location["street"]
            item["website"] = "https://www.huntingandfishing.co.nz/store-locator/" + item["ref"]
            item["opening_hours"] = OpeningHours()
            hours_dict = json.loads(location["working_hours"])
            for day, hours_range in hours_dict.items():
                if not hours_range.get("from") or not hours_range.get("to"):
                    continue
                item["opening_hours"].add_range(day.title(), hours_range["from"], hours_range["to"])
            apply_category(Categories.SHOP_OUTDOOR, item)
            yield item
