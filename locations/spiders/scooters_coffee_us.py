from locations.storefinders.metalocator import MetaLocatorSpider

# Note: the "storecode" field in source data has duplicates thus
# it cannot be used as a reference. The "id" field assigned by
# MetaLocator is used instead.


class ScootersCoffeeUSSpider(MetaLocatorSpider):
    name = "scooters_coffee_us"
    item_attributes = {"brand": "Scooter's Coffee", "brand_wikidata": "Q117280308"}
    brand_id = "12991"
    country_list = ["United States"]
