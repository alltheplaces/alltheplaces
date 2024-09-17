from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class AdriaticFurnitureAUSpider(WPStoreLocatorSpider):
    name = "adriatic_furniture_au"
    item_attributes = {
        "brand": "Adriatic Furniture",
        "brand_wikidata": "Q117856796",
        "extras": Categories.SHOP_FURNITURE.value,
    }
    allowed_domains = ["www.adriatic.com.au"]
    days = DAYS_EN
