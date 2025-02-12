from locations.storefinders.dominos_pizza_international import DominosPizzaInternationalSpider


class DominosPizzaKNSpider(DominosPizzaInternationalSpider):
    name = "dominos_pizza_kn"
    region_code = "KN"
    dpz_market = "ST_KITTS"
    domain = "order.golo01.dominos.com"
