import re

from locations.storefinders.stockist import StockistSpider
from locations.categories import Categories
from locations.hours import OpeningHours

class MintVelvetGBSpider(StockistSpider):
    name = "mint_velvet_gb"
    item_attributes = {"brand": "Mint Velvet", "brand_wikidata": "Q104901572","extras": Categories.SHOP_CLOTHES.value}
    key="u10125"
