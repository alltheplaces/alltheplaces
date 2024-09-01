from locations.categories import Categories
from locations.storefinders.storerocket import StoreRocketSpider


class JetGBSpider(StoreRocketSpider):
    name = "jet_gb"
    item_attributes = {"brand": "JET", "brand_wikidata": "Q568940", "extras": Categories.FUEL_STATION.value}
    storerocket_id = "2BkJ1wEpqR"
    base_url = "https://www.jetlocal.co.uk/drivers/locator"
