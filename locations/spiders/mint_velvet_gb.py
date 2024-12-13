from locations.categories import Categories
from locations.storefinders.stockist import StockistSpider


class MintVelvetGBSpider(StockistSpider):
    name = "mint_velvet_gb"
    item_attributes = {"brand": "Mint Velvet", "brand_wikidata": "Q104901572", "extras": Categories.SHOP_CLOTHES.value}
    key = "u10125"

    def parse_item(self, item, location):
        if "Boutique" in item["name"]:
            yield item
