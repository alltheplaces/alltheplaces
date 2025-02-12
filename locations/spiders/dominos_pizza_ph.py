from locations.storefinders.dominos_pizza_international import DominosPizzaInternationalSpider


class DominosPizzaPHSpider(DominosPizzaInternationalSpider):
    name = "dominos_pizza_ph"
    region_code = "PH"
    dpz_market = "PHILIPPINES"
    domain = "order.golo01.dominos.com"
