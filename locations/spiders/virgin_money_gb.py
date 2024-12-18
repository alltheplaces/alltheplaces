from locations.storefinders.woosmap import WoosmapSpider


class VirginMoneyGBSpider(WoosmapSpider):
    name = "virgin_money_gb"
    item_attributes = {
        "brand_wikidata": "Q2527746",
        "brand": "Virgin Money",
    }
    key = "woos-89a9a4a8-799f-3cbf-9917-4e7b88e46c30"
    origin = "https://uk.virginmoney.com"
