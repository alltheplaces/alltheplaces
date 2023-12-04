from locations.spiders.burger_king import BurgerKingSpider
from locations.storefinders.amrest_eu import AmrestEUSpider


class BurgerKingCZSpider(AmrestEUSpider):
    name = "burger_king_cz"
    item_attributes = BurgerKingSpider.item_attributes
    base_urls = ["https://api.amrest.eu/amdv/ordering-api/BK_CZ/"]
