from locations.categories import Categories, Extras, Fuel, apply_yes_no
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class RoyalFarmsSpider(WPStoreLocatorSpider):
    name = "royal_farms"
    item_attributes = {"brand": "Royal Farms", "brand_wikidata": "Q7374169", "extras": Categories.FUEL_STATION.value}
    allowed_domains = ["royalfarms.com"]
    searchable_points_files = ["us_centroids_10mile_radius_state.csv"]
    area_field_filter = ["MD", "DE", "VA", "PA", "NJ", "WV", "NC"]
    search_radius = 10
    max_results = 50

    def post_process_item(self, item, response, store):
        amenities = store.get("terms")
        if "Coming Soon" in amenities:
            return
        apply_yes_no(Extras.CAR_WASH, item, "Carwash" in amenities)
        apply_yes_no(Fuel.DIESEL, item, "Diesel Fuel" in amenities)
        apply_yes_no(Fuel.E15, item, "Ethanol 15 Percent" in amenities)
        apply_yes_no(Fuel.E85, item, "Flex Fuel" in amenities)
        apply_yes_no(Fuel.ELECTRIC, item, "EV Charging" in amenities)
        yield item
