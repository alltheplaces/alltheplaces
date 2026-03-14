from locations.categories import Categories
from locations.storefinders.storerocket import StoreRocketSpider


class MapcoUSSpider(StoreRocketSpider):
    name = "mapco_us"
    storerocket_id = "5Z4wZoKpPd"
    item_attributes = {"brand": "Mapco", "brand_wikidata": "Q107589462", "extras": Categories.FUEL_STATION.value}
