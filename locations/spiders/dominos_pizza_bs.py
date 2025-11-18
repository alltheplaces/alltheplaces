from locations.storefinders.dominos_pizza_international import DominosPizzaInternationalSpider


class DominosPizzaBSSpider(DominosPizzaInternationalSpider):
    name = "dominos_pizza_bs"
    region_code = "BS"
    dpz_market = "BAHAMAS"
    domain = "order.golo04.dominos.com"
