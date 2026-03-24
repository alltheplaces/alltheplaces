import re
from typing import Iterable

from scrapy.http import Request, Response

from locations.categories import Categories, Extras, PaymentMethods, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
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
        item["addr_full"] = re.sub(r",\s*0+\s*,", ",", item["addr_full"])  # Clean invalid postcodes e.g. 00000
        item["branch"] = item.pop("name").removeprefix("Debonairs Pizza ")
        attributes = [attribute["value"] for attribute in feature["attributes"]]

        apply_yes_no(Extras.DELIVERY, item, "Delivery" in attributes)
        apply_yes_no(PaymentMethods.CARDS, item, "Card" in attributes)
        apply_yes_no(PaymentMethods.DEBIT_CARDS, item, "Debit cards" in attributes)
        apply_yes_no(PaymentMethods.CREDIT_CARDS, item, "Credit cards" in attributes)
        apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive-through" in attributes)
        apply_yes_no(Extras.BREAKFAST, item, "Breakfast" in attributes)
        apply_yes_no(Extras.BRUNCH, item, "Brunch" in attributes)
        apply_yes_no(Extras.LUNCH, item, "Lunch" in attributes)
        apply_yes_no(Extras.WHEELCHAIR, item, "Wheelchair accessible entrance" in attributes)

        for attribute in attributes:
            self.crawler.stats.inc_value(f"atp/{self.name}/attribute/{attribute}")

        apply_category(Categories.FAST_FOOD, item)

        yield Request(url=item["website"], cb_kwargs={"item": item}, callback=self.parse_opening_hours)

    def parse_opening_hours(self, response: Response, item: Feature) -> Iterable[Feature]:
        item["opening_hours"] = OpeningHours()
        for rule in response.xpath('//*[contains(@class, "operating-hours-day")]'):
            day = rule.xpath("./text()").get("")
            hours = rule.xpath("./following-sibling::span/text()").get("").replace("|", "to")
            item["opening_hours"].add_ranges_from_string(f"{day} {hours}")
        yield item
