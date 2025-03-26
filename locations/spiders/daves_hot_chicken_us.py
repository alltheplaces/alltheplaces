from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Extras, PaymentMethods, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class DavesHotChickenUSSpider(JSONBlobSpider):
    name = "daves_hot_chicken_us"
    item_attributes = {"brand": "Dave's Hot Chicken", "brand_wikidata": "Q108292298"}
    allowed_domains = ["daveshotchicken.com"]
    start_urls = ["https://daveshotchicken.com/api/v2/locations"]
    locations_key = "locations"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if not feature["available"]:
            return
        item["street_address"] = item.pop("addr_full", None)
        item["opening_hours"] = OpeningHours()
        for day_hours in feature["hours"]:
            item["opening_hours"].add_range(day_hours["day"].title(), day_hours["open"], day_hours["close"])
        apply_category(Categories.FAST_FOOD, item)
        apply_yes_no(Extras.DRIVE_THROUGH, item, feature["services"]["drivethru"], False)
        apply_yes_no(Extras.DELIVERY, item, feature["services"]["delivery"], False)
        apply_yes_no(Extras.TAKEAWAY, item, feature["services"]["pickup"], False)
        apply_yes_no(Extras.INDOOR_SEATING, item, feature["services"]["dinein"], False)

        # Use a very cautious approach of not assuming the absence of a
        # payment method in an array of payment method types means the
        # store doesn't accept that payment method. Payment method
        # information is not shown on the website for each location. All
        # stores are observed to accept all four payment method types listed
        # below so this cautious approach likely has no real world impact.
        card_types = feature["payments"]["cardtypes"]
        apply_yes_no(PaymentMethods.AMERICAN_EXPRESS, item, "American Express" in card_types)
        apply_yes_no(PaymentMethods.DISCOVER_CARD, item, "Discover" in card_types)
        apply_yes_no(PaymentMethods.MASTER_CARD, item, "MasterCard" in card_types)
        apply_yes_no(PaymentMethods.VISA, item, "Visa" in card_types)

        yield item
