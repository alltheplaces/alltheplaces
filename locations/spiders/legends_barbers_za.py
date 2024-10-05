from locations.storefinders.yith import YithSpider


class LegendsBarbersZASpider(YithSpider):
    name = "legends_barbers_za"
    item_attributes = {
        "brand": "Legends Barber",
        "brand_wikidata": "Q116895407",
    }
    allowed_domains = ["legends-barber.com"]

