from locations.hours import DAYS_ES
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class VerticheMXSpider(WPStoreLocatorSpider):
    name = "vertiche_mx"
    item_attributes = {"brand": "Vertiche", "brand_wikidata": "Q113215945"}
    allowed_domains = ["vertiche.mx"]
    iseadgg_countries_list = ["MX"]
    search_radius = 24
    max_results = 25
    days = DAYS_ES
