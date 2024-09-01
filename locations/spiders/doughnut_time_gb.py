from locations.storefinders.stockist import StockistSpider


class DoughnutTimeGBSpider(StockistSpider):
    name = "doughnut_time_gb"
    item_attributes = {
        "brand_wikidata": "Q117286917",
        "brand": "Doughnut Time",
    }
    key = "u22659"
