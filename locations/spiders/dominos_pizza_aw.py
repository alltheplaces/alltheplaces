from locations.storefinders.dominos_pizza_international import DominosPizzaInternationalSpider


class DominosPizzaAWSpider(DominosPizzaInternationalSpider):
    name = "dominos_pizza_aw"
    region_code = "AW"
    dpz_market = "ARUBA"
    domain = "order.golo01.dominos.com"
