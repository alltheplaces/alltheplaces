from locations.categories import Categories
from locations.storefinders.elfsight import ElfsightSpider


class PuebloPRSpider(ElfsightSpider):
    name = "pueblo_pr"
    item_attributes = {
        "brand": "Pueblo",
        "brand_wikidata": "Q7258464",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    host = "core.service.elfsight.com"
    api_key = "cf19e95f-dbcc-4213-a471-329628e371f9"
