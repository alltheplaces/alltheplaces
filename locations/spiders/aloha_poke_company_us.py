from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class AlohaPokeCompanyUSSpider(WPStoreLocatorSpider):
    name = "aloha_poke_company_us"
    item_attributes = {"brand_wikidata": "Q111231031", "brand": "Aloha Pokē Co", "extras": Categories.FAST_FOOD.value}
    allowed_domains = [
        "www.alohapokeco.com",
    ]
    days = DAYS_EN
