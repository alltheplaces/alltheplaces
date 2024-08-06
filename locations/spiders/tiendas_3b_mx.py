from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class Tiendas3BMXSpider(AgileStoreLocatorSpider):
    name = "tiendas_3b_mx"
    item_attributes = {
        "brand_wikidata": "Q113217378",
        "brand": "Tiendas 3B",
    }
    allowed_domains = [
        "tiendas3b.com",
    ]