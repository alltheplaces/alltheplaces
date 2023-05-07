from locations.storefinders.storepoint import StorepointSpider


class SimpleSimonsPizzaUSSpider(StorepointSpider):
    name = "simple_simons_pizza_us"
    item_attributes = {"brand": "Simple Simon's Pizza", "brand_wikidata": "Q116737866"}
    key = "15dbb16b507995"
