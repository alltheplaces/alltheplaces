from locations.categories import Categories
from locations.storefinders.sylinder import SylinderSpider


class DeliDeLucaNOSpider(SylinderSpider):
    name = "deli_de_luca_no"
    item_attributes = {
        "brand": "Deli de Luca",
        "brand_wikidata": "Q11965047",
        "extras": Categories.SHOP_CONVENIENCE.value,
    }
    app_key = "1800"
    base_url = "https://delideluca.no/finn-oss/#"  # Kind of a hack. The website doesn't have the storefinder in place.
