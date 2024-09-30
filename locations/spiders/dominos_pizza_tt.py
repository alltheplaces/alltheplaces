from locations.storefinders.dominos_pizza_international import DominosPizzaInternationalSpider


class DominosPizzaTTSpider(DominosPizzaInternationalSpider):
    name = "dominos_pizza_tt"
    region_code = "TT"
    dpz_market = "TRINIDAD"
    domain = "order.golo01.dominos.com"
