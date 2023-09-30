from locations.storefinders.yext import YextSpider


class CaribouCoffeeUSSpider(YextSpider):
    name = "caribou_coffee_us"
    item_attributes = {"brand": "Caribou Coffee", "brand_wikidata": "Q5039494"}
    api_key = "c328ae6d84635fc2bd9c91497cdeedc0"
    api_version = "20220511"
