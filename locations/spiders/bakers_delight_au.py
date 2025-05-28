from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.storefinders.algolia import AlgoliaSpider


class BakersDelightAUSpider(AlgoliaSpider):
    name = "bakers_delight_au"
    item_attributes = {"brand": "Bakers Delight", "brand_wikidata": "Q4849261"}
    api_key = "5b1eaa9c00c3888446cba6eae1a94918"
    app_id = "CLITZSTYQ0"
    index_name = "prd_sod_location"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["id"])
        item["branch"] = item.pop("name", None)
        item["addr_full"] = feature["formatted_address"]["display"]
        item["phone"] = feature["phone_number"]["display"]
        item["website"] = "https://www.bakersdelight.com.au" + feature["url"]

        if hours := feature.get("opening_hours"):
            item["opening_hours"] = OpeningHours()
            for day_hours in hours:
                item["opening_hours"].add_range(DAYS_EN[day_hours["day"].title()], day_hours["open"], day_hours["close"])

        apply_category(Categories.SHOP_BAKERY, item)
        yield item
