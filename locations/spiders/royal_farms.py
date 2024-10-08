import scrapy

from locations.categories import Categories, Extras, Fuel, apply_yes_no
from locations.dict_parser import DictParser
from locations.geo import point_locations


class RoyalFarmsSpider(scrapy.Spider):
    name = "royal_farms"
    item_attributes = {"brand": "Royal Farms", "brand_wikidata": "Q7374169", "extras": Categories.FUEL_STATION.value}
    allowed_domains = ["royalfarms.com"]

    def start_requests(self):
        for state in ["MD", "DE", "VA", "PA", "NJ", "NC"]:
            for lat, lon in point_locations("us_centroids_10mile_radius_state.csv", state):
                yield scrapy.Request(
                    url=f"https://www.royalfarms.com/wp-admin/admin-ajax.php?action=store_search&lat={lat}&lng={lon}&max_results=50&search_radius=10",
                )

    def parse(self, response):
        for store in response.json():
            store["street_address"] = store.pop("address")
            item = DictParser.parse(store)
            amenities = store.get("terms")
            if "Coming Soon" in amenities:
                continue
            apply_yes_no(Extras.CAR_WASH, item, "Carwash" in amenities)
            apply_yes_no(Fuel.DIESEL, item, "Diesel Fuel" in amenities)
            apply_yes_no(Fuel.E15, item, "Ethanol 15 Percent" in amenities)
            apply_yes_no(Fuel.E85, item, "Flex Fuel" in amenities)
            apply_yes_no(Fuel.ELECTRIC, item, "EV Charging" in amenities)
            yield item
