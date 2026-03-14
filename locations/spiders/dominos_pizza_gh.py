from locations.storefinders.dominos_pizza_international import DominosPizzaInternationalSpider


class DominosPizzaGHSpider(DominosPizzaInternationalSpider):
    name = "dominos_pizza_gh"
    region_code = "GH"
    dpz_market = "GHANA"
