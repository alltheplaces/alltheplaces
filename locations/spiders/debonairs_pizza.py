from typing import Iterable

from scrapy.http import Request, Response

from locations.categories import Categories, Extras, PaymentMethods, apply_category, apply_yes_no
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser
from locations.storefinders.go_review_api import GoReviewApiSpider

DEBONAIRS_SHARED_ATTRIBUTES = {"brand": "Debonairs Pizza", "brand_wikidata": "Q65079407"}


class DebonairsPizzaSpider(GoReviewApiSpider):
    name = "debonairs_pizza"
    item_attributes = DEBONAIRS_SHARED_ATTRIBUTES

    domain_list = [
        "locations.debonairspizza.co.za",
        "botswanalocations.debonairspizza.africa",
        "kenyalocations.debonairspizza.africa",
        # "malawilocations.debonairspizza.africa", # website exists, but has no stores as of 2025-08-30
        "mauritiuslocations.debonairspizza.africa",
        "zambialocations.debonairspizza.africa",
    ]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Request]:
        yield Request(
            url=item["website"],
            meta={"item": item, "attributes": feature.get("attributes")},
            callback=self.parse_location_ld,
        )

    def parse_location_ld(self, response) -> Iterable[Feature]:
        ld_item = LinkedDataParser.parse(response, "Restaurant")

        ld_item["ref"] = response.meta["item"]["ref"]
        ld_item["branch"] = ld_item.pop("name").removeprefix("Debonairs Pizza ")

        if ld_item.get("postcode") is not None and int(ld_item.get("postcode")) == 0:
            ld_item.pop("postcode")

        if response.meta["attributes"] is not None:
            attributes = [attribute["value"] for attribute in response.meta["attributes"]]

            apply_yes_no(Extras.DELIVERY, ld_item, "Delivery" in attributes)
            apply_yes_no(PaymentMethods.CARDS, ld_item, "Card" in attributes)
            apply_yes_no(PaymentMethods.DEBIT_CARDS, ld_item, "Debit cards" in attributes)
            apply_yes_no(PaymentMethods.CREDIT_CARDS, ld_item, "Credit cards" in attributes)
            apply_yes_no(Extras.DRIVE_THROUGH, ld_item, "Drive-through" in attributes)
            apply_yes_no(Extras.BREAKFAST, ld_item, "Breakfast" in attributes)
            apply_yes_no(Extras.BRUNCH, ld_item, "Brunch" in attributes)
            apply_yes_no(Extras.LUNCH, ld_item, "Lunch" in attributes)
            apply_yes_no(Extras.WHEELCHAIR, ld_item, "Wheelchair accessible entrance" in attributes)

            for attribute in attributes:
                self.crawler.stats.inc_value(f"atp/{self.name}/attribute/{attribute}")

        apply_category(Categories.FAST_FOOD, ld_item)

        yield ld_item
