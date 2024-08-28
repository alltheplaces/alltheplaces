from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class PharmasaveAUSpider(WPStoreLocatorSpider):
    name = "pharmasave_au"
    item_attributes = {"brand": "PharmaSave", "brand_wikidata": "Q63367906", "extras": Categories.PHARMACY.value}
    allowed_domains = ["www.pharmasave.com.au"]
    days = DAYS_EN
