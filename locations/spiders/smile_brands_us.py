from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class SmileBrandsUSSpider(WPStoreLocatorSpider):
    name = "smile_brands_us"
    item_attributes = {"brand": "Smile Brands Inc.", "brand_wikidata": "Q108286823", "extras": Categories.DENTIST.value}
    allowed_domains = ["smilebrands.com"]
    days = DAYS_EN
