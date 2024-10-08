from locations.storefinders.freshop import FreshopSpider


class DagostinoUSSpider(FreshopSpider):
    name = "dagostino_us"
    item_attributes = {
        "brand_wikidata": "Q20656844",
        "brand": "D'Agostino",
    }
    app_key = "dagostino"
