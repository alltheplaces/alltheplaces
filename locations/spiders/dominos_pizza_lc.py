from locations.storefinders.dominos_pizza_international import DominosPizzaInternationalSpider


class DominosPizzaLCSpider(DominosPizzaInternationalSpider):
    name = "dominos_pizza_lc"
    region_code = "LC"
    dpz_market = "ST_LUCIA"
    domain = "order.golo01.dominos.com"
