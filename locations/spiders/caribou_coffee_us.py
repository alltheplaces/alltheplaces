from locations.categories import Categories, Extras, apply_yes_no
from locations.storefinders.yext_answers import YextAnswersSpider


class CaribouCoffeeUSSpider(YextAnswersSpider):
    name = "caribou_coffee_us"
    item_attributes = {"brand": "Caribou Coffee", "brand_wikidata": "Q5039494", "extras": Categories.CAFE.value}
    api_key = "c328ae6d84635fc2bd9c91497cdeedc0"
    experience_key = "location-search"

    def parse_item(self, location, item):
        item["website"] = location["data"].get("c_pagesURL")

        amenities_part_1 = [v for v in location["data"].get("c_amenities", [])]
        amenities_part_2 = [v for v in location["data"].get("c_storeAmenities", [])]
        amenities = amenities_part_1 + list(set(amenities_part_2) - set(amenities_part_1))
        apply_yes_no(Extras.WIFI, item, "WiFi" in amenities, False)
        apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive-Thru" in amenities, False)
        apply_yes_no(Extras.INDOOR_SEATING, item, "Indoor Seating" in amenities, False)

        yield item
