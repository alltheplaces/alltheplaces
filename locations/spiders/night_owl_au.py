from locations.storefinders.storerocket import StoreRocketSpider


class NightOwlAUSpider(StoreRocketSpider):
    name = "night_owl_au"
    item_attributes = {"brand": "NightOwl", "brand_wikidata": "Q7033183"}
    storerocket_id = "xk4YPX0pXa"
    base_url = "https://nightowl.com.au/store-locator/"
