from typing import Iterable

from scrapy.http import Request, Response

from locations.categories import Categories, Extras, PaymentMethods, apply_category, apply_yes_no
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser
from locations.storefinders.go_review_api import GoReviewApiSpider


class FishawaysZASpider(GoReviewApiSpider):
    name = "fishaways_za"
    item_attributes = {"brand": "Fishaways", "brand_wikidata": "Q116618989"}

    domain = "locations.fishaways.co.za"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Request]:
        yield Request(
            url=item["website"],
            meta={"item": item, "attributes": feature.get("attributes")},
            callback=self.parse_location_ld,
        )

    def parse_location_ld(self, response) -> Iterable[Feature]:
        ld_item = LinkedDataParser.parse(response, "Restaurant")

        ld_item["ref"] = response.meta["item"]["ref"]
        ld_item["branch"] = ld_item.pop("name").removeprefix("Fishaways ")

        if response.meta["attributes"] is not None:
            attributes = [attribute["value"] for attribute in response.meta["attributes"]]

            apply_yes_no(Extras.DELIVERY, ld_item, "Delivery" in attributes)
            apply_yes_no(PaymentMethods.CARDS, ld_item, "Card" in attributes)
            apply_yes_no(PaymentMethods.DEBIT_CARDS, ld_item, "Debit cards" in attributes)
            apply_yes_no(PaymentMethods.CREDIT_CARDS, ld_item, "Credit cards" in attributes)
            apply_yes_no(Extras.DRIVE_THROUGH, ld_item, "Drive-through" in attributes)
            apply_yes_no(Extras.DRIVE_THROUGH, ld_item, "Drive Thru" in attributes)
            apply_yes_no(Extras.BREAKFAST, ld_item, "Breakfast" in attributes)
            apply_yes_no(Extras.BRUNCH, ld_item, "Brunch" in attributes)

        apply_category(Categories.FAST_FOOD, ld_item)

        yield ld_item
