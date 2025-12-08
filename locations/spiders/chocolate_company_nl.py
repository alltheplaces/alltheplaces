from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class ChocolateCompanyNLSpider(WPStoreLocatorSpider):
    name = "chocolate_company_nl"
    item_attributes = {"brand_wikidata": "Q108926938", "brand": "Chocolate Company", "extras": Categories.CAFE.value}
    allowed_domains = [
        "choco.piranha-dev.online",
    ]
    days = DAYS_EN
