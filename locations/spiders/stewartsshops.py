from locations.categories import Categories, apply_category
from locations.spiders.costacoffee_gb import yes_or_no
from locations.storefinders.momentfeed import MomentFeedSpider


class StewartsShopsSpider(MomentFeedSpider):
    name = "stewartsshops"
    item_attributes = {"brand_wikidata": "Q7615690"}
    id = "ZGRQTRLWHXDMDNUO"

    def parse_item(self, item, feature, store_info, **kwargs):
        item["website"] = f'https://locations.stewartsshops.com{feature["llp_url"]}'
        fields = {entry["name"]: entry["data"] for entry in feature["custom_fields"]}
        item["extras"] = {
            "fuel:diesel": yes_or_no("Diesel" in fields),
            "fuel:e0_octane_91": yes_or_no("Gas Station with 91 Premium Non-Ethanol" in fields),
            "fuel:kerosene": yes_or_no("Kerosene" in fields),
            "atm": yes_or_no("ATM" in fields),
            "toilets": yes_or_no("Restroom" in fields),
            "car_wash": yes_or_no("Car Wash" in fields),
        }

        if "Gas Station" in fields:
            apply_category(Categories.FUEL_STATION, item)
        else:
            apply_category(Categories.SHOP_CONVENIENCE, item)

        yield item
