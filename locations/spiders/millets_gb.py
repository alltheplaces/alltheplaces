from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class MilletsGBSpider(JSONBlobSpider):
    name = "millets_gb"
    item_attributes = {"brand": "Millets", "brand_wikidata": "Q64822903"}
    start_urls = ["https://extensions.millets.co.uk/api/stores?lat=54.5&lng=-3&radius=2000&limit=500"]
    locations_key = "stores"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["street_address"] = merge_address_lines([feature["address_1"], feature["address_2"]])
        item["phone"] = feature.get("local_phone")
        item["website"] = "https://www.millets.co.uk/pages/store/" + item["name"].lower().replace(" ", "-").replace(
            "\xa0", "-"
        )
        item["branch"] = item.pop("name").removeprefix("Millets").strip()
        item["opening_hours"] = self.parse_opening_hours(feature["hours_sets"]["primary"]["days"])
        apply_category(Categories.SHOP_OUTDOOR, item)

        yield item

    def parse_opening_hours(self, rules: dict) -> OpeningHours:
        oh = OpeningHours()
        for day, times in rules.items():
            for rule in times:
                oh.add_range(day, rule["open"], rule["close"])
        return oh
