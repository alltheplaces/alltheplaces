from locations.storefinders.closeby import ClosebySpider


class UniversalStoreAUSpider(ClosebySpider):
    name = "universal_store_au"
    item_attributes = {"brand": "Universal Store", "brand_wikidata": "Q96412731"}
    api_key = "87aa802ed1754c56a156df516b2d65ed"
