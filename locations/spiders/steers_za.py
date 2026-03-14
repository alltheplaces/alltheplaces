from typing import Iterable

from scrapy.http import Request, Response

from locations.categories import Categories, Extras, PaymentMethods, apply_category, apply_yes_no
from locations.items import Feature
from locations.storefinders.go_review_api import GoReviewApiSpider


class SteersZASpider(GoReviewApiSpider):
    name = "steers_za"
    item_attributes = {"brand": "Steers", "brand_wikidata": "Q3056765"}

    domain = "locations.steers.co.za"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Request]:
        item["branch"] = item.pop("name").removeprefix("Steers ")
        if feature.get("attributes") is not None:
            attributes = [attribute["value"] for attribute in feature["attributes"]]
            apply_yes_no(Extras.DELIVERY, item, "Delivery" in attributes)
            apply_yes_no(PaymentMethods.CARDS, item, "Card" in attributes)
            apply_yes_no(PaymentMethods.DEBIT_CARDS, item, "Debit cards" in attributes)
            apply_yes_no(PaymentMethods.CREDIT_CARDS, item, "Credit cards" in attributes)
            apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive-through" in attributes)
            apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive Thru" in attributes)
            apply_yes_no(Extras.BREAKFAST, item, "Breakfast" in attributes)
            apply_yes_no(Extras.BRUNCH, item, "Brunch" in attributes)

            for attribute in attributes:
                self.crawler.stats.inc_value(f"atp/{self.name}/attribute/{attribute}")

        apply_category(Categories.FAST_FOOD, item)

        yield item
