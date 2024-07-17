from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.storefinders.momentfeed import MomentFeedSpider


class StewartsShopsSpider(MomentFeedSpider):
    name = "stewarts_shops"
    item_attributes = {"brand_wikidata": "Q7615690"}
    id = "ZGRQTRLWHXDMDNUO"

    def parse_item(self, item, feature, store_info, **kwargs):
        item["website"] = f'https://locations.stewartsshops.com{feature["llp_url"]}'
        fields = {entry["name"]: entry["data"] for entry in feature["custom_fields"]}
        apply_yes_no(Fuel.DIESEL, item, "Diesel" in fields, False)
        apply_yes_no(Fuel.OCTANE_91, item, "Gas Station with 91 Premium Non-Ethanol" in fields, False)
        apply_yes_no(Fuel.KEROSENE, item, "Kerosene" in fields, False)
        apply_yes_no(Extras.ATM, item, "ATM" in fields, False)
        apply_yes_no(Extras.TOILETS, item, "Restroom" in fields, False)
        apply_yes_no(Extras.CAR_WASH, item, "Car Wash" in fields, False)

        if "Gas Station" in fields:
            apply_category(Categories.FUEL_STATION, item)
        else:
            apply_category(Categories.SHOP_CONVENIENCE, item)

        yield item
