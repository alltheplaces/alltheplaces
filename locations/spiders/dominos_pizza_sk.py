from locations.storefinders.dominos_pizza_international import DominosPizzaInternationalSpider


class DominosPizzaSKSpider(DominosPizzaInternationalSpider):
    name = "dominos_pizza_sk"
    region_code = "SK"
    dpz_market = "SLOVAKIA"
    search_radius = 1000000
