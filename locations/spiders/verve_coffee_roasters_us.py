from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, DAYS_EN
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class VerveCoffeeRoastersUSSpider(JSONBlobSpider):
    name = "verve_coffee_roasters_us"
    item_attributes = {"brand": "Verve Coffee Roasters", "brand_wikidata": "Q17030230"}
    allowed_domains = ["cdn5.editmysite.com"]
    start_urls = ["https://cdn5.editmysite.com/app/store/api/v28/editor/users/131224020/sites/408214956867749809/store-locations"]
    locations_key = "data"

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature["address"].pop("data"))
        feature.pop("address", None)

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["id"]
        item["branch"] = feature["business_name"].removeprefix("Verve Coffee ")
        item.pop("name", None)
        item["street_address"] = merge_address_lines([feature.get("street"), feature.get("street2")])
        item.pop("street", None)
        item.pop("email", None)  # Not store specific.
        item["opening_hours"] = OpeningHours()
        for day_name, day_hours in feature["pickup_hours"].items():
            for time_range in day_hours:
                item["opening_hours"].add_range(DAYS_EN[day_name.title()], time_range["open"], time_range["close"], "%H:%M:%S")
        apply_category(Categories.COFFEE_SHOP, item)
        yield item
