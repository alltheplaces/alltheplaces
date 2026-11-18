from typing import Any

from pycountry import subdivisions
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider

US_STATES = {subdivision.code.removeprefix("US-") for subdivision in subdivisions.get(country_code="US")}


class MaggianosLittleItalySpider(JSONBlobSpider):
    name = "maggianos_little_italy"
    item_attributes = {"brand": "Maggiano's Little Italy", "brand_wikidata": "Q6730149"}
    allowed_domains = ["green.maggianos.com"]
    start_urls = [
        f"https://green.maggianos.com/api/v1/search/restaurants/by-state?state={state}" for state in US_STATES
    ]

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("properties"))
        feature.update(feature.pop("geometry")["coordinates"])
        feature["address"] = feature.pop("slug")
        feature["address"]["country"] = feature.pop("country")

    def post_process_item(self, item: Feature, response: Response, feature: dict, **kwargs: Any) -> Any:
        if feature["status"] != "O":
            return
        item["branch"] = item.pop("name")
        item["website"] = "https://www.maggianos.com/locations/{}/{}/{}".format(
            feature["address"]["state"].lower().replace(" ", "-"),
            feature["address"]["city"].lower().replace(" ", "-"),
            feature["urlSlug"],
        )
        item["opening_hours"] = OpeningHours()
        for rule in feature["storeHours"]:
            item["opening_hours"].add_range(rule["dayName"], rule["openTime"], rule["endTime"])
        apply_category(Categories.RESTAURANT, item)
        yield item
