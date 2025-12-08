from locations.storefinders.stockist import StockistSpider


class WorkWorldUSSpider(StockistSpider):
    name = "work_world_us"
    item_attributes = {
        "brand_wikidata": "Q113502525",
        "brand": "Work World",
    }
    key = "u9787"
