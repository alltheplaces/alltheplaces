import json

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class LindtSpider(JSONBlobSpider):
    name = "lindt"
    item_attributes = {
        "brand": "Lindt",
        "brand_wikidata": "Q152822",
    }
    start_urls = ["https://www.lindt-spruengli.com/stores/"]

    def extract_json(self, response):
        return DictParser.get_nested_key(
            json.loads(response.xpath('//script[contains(text(), "locationItems")]/text()').get()), "locationItems"
        )

    def post_process_item(self, item, response, location):
        item["street_address"] = item.pop("street")

        oh = OpeningHours()
        for day in DAYS_FULL:
            day_hours = location[f"opening_hours_{day.lower()}"]
            oh.add_ranges_from_string(f"{day} {day_hours}")
        item["opening_hours"] = oh

        if "ghirardelli" in item["name"].casefold():
            item["brand"] = "Ghirardelli"
            item["brand_wikidata"] = "Q1134349"

        apply_category(Categories.SHOP_CHOCOLATE, item)
        yield item
