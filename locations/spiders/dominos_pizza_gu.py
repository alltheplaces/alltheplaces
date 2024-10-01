from locations.storefinders.dominos_pizza_international import DominosPizzaInternationalSpider


class DominosPizzaGUSpider(DominosPizzaInternationalSpider):
    name = "dominos_pizza_gu"
    region_code = "GU"
    dpz_market = "GUAM"
    domain = "order.golo01.dominos.com"
