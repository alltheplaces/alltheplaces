from locations.storefinders.dominos_pizza_international import DominosPizzaInternationalSpider


class DominosPizzaJMSpider(DominosPizzaInternationalSpider):
    name = "dominos_pizza_jm"
    region_code = "JM"
    dpz_market = "JAMAICA"
    domain = "order.golo01.dominos.com"
    city_search = True
