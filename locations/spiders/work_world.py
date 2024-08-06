from locations.storefinders.stockist import StockistSpider


class WorkWorldSpider(StockistSpider):
    name = "work_world"
    item_attributes = {
        "brand_wikidata": "Q113502525",
        "brand": "Work World",
    }
    key = "u9787"
