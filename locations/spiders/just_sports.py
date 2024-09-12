from locations.storefinders.stockist import StockistSpider


class JustSportsSpider(StockistSpider):
    name = "just_sports"
    item_attributes = {
        "brand_wikidata": "Q110677242",
        "brand": "Just Sports",
    }
    key = "u12231"
