from locations.storefinders.storepoint import StorepointSpider


class DanielsDonutsAUSpider(StorepointSpider):
    name = "daniels_donuts_au"
    item_attributes = {"brand": "Daniel's Donuts", "brand_wikidata": "Q116147181"}
    key = "1614a61b80e685"
