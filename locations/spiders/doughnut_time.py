from locations.storefinders.stockist import StockistSpider


class DoughnutTimeSpider(StockistSpider):
    name = "doughnut_time"
    item_attributes = {
        "brand_wikidata": "Q117286917",
        "brand": "Doughnut Time",
    }
    key = "u22659"