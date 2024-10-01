from locations.storefinders.dominos_pizza_international import DominosPizzaInternationalSpider


class DominosPizzaSXSpider(DominosPizzaInternationalSpider):
    name = "dominos_pizza_sx"
    region_code = "SX"
    dpz_market = "ST_MAARTEN"
    domain = "order.golo01.dominos.com"
