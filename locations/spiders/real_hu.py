from locations.categories import Categories
from locations.hours import DAYS_HU
from locations.storefinders.maps_marker_pro import MapsMarkerProSpider


class RealHU(MapsMarkerProSpider):
    name = "real_hu"
    allowed_domains = ["real.hu"]
    days = DAYS_HU
    item_attributes = {"brand": "Real", "brand_wikidata": "Q100741414", "extras": Categories.SHOP_CONVENIENCE.value}
