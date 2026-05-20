from itertools import islice
from typing import Iterable

from chompjs import parse_js_objects
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class SteineckeDESpider(JSONBlobSpider):
    name = "steinecke_de"
    item_attributes = {"brand": "Steinecke", "brand_wikidata": "Q57516278"}
    start_urls = ["https://www.steinecke.info/standorte/"]

    def extract_json(self, response: TextResponse) -> dict | list[dict]:
        js_objects = parse_js_objects(response.xpath('//script/text()[contains(., "locations_data")]').get())
        return next(islice(js_objects, 1, None))

    def post_process_item(self, item: Feature, response: TextResponse, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["ref"] = item["website"] = location["permalink"]

        try:
            item["opening_hours"] = self.parse_opening_hours(location["opening_hours"])
        except Exception:
            pass

        apply_category(Categories.SHOP_BAKERY, item)

        yield item

    def parse_opening_hours(self, rules: dict) -> OpeningHours:
        opening_hours = OpeningHours()
        for day, hour_range in rules.items():
            if hour_range:
                opening_hours.add_range(day, *hour_range.split("-"))
        return opening_hours
