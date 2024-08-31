from locations.storefinders.stockist import StockistSpider


class BlueIllusionAUNZSpider(StockistSpider):
    name = "blue_illusion_au_nz"
    item_attributes = {
        "brand_wikidata": "Q118464703",
        "brand": "Blue Illusion",
    }
    key = "u17747"
