from locations.storefinders.dominos_pizza_international import DominosPizzaInternationalSpider


class DominosPizzaMUSpider(DominosPizzaInternationalSpider):
    name = "dominos_pizza_mu"
    region_code = "MU"
    dpz_market = "MAURITIUS"
