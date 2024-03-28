from locations.categories import Categories
from locations.storefinders.sylinder import SylinderSpider


class SparNoSpider(SylinderSpider):
    name = "spar_no"
    item_attributes = {
        "brand": "Spar",
        "brand_wikidata": "Q610492",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    app_key = "1210"
    base_url = "https://spar.no/Finn-butikk/"
