from locations.categories import Categories
from locations.storefinders.wp_go_maps import WPGoMapsSpider


class SonicCASpider(WPGoMapsSpider):
    name = "sonic_ca"
    item_attributes = {"brand": "Sonic", "brand_wikidata": "Q118669677", "extras": Categories.FUEL_STATION.value}
    allowed_domains = ["energiesonic.com"]
