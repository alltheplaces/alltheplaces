from locations.categories import Categories
from locations.hours import DAYS_HU
from locations.storefinders.maps_marker_pro import MapsMarkerProSpider


class RealHUSpider(MapsMarkerProSpider):
    name = "real_hu"
    item_attributes = {"brand": "Reál", "brand_wikidata": "Q100741414", "extras": Categories.SHOP_CONVENIENCE.value}
    allowed_domains = ["real.hu"]
    days = DAYS_HU
