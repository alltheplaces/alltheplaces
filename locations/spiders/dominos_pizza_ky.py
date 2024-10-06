from locations.storefinders.dominos_pizza_international import DominosPizzaInternationalSpider


class DominosPizzaKYSpider(DominosPizzaInternationalSpider):
    name = "dominos_pizza_ky"
    region_code = "KY"
    dpz_market = "CAYMAN_ISLANDS"
    domain = "order.golo01.dominos.com"
