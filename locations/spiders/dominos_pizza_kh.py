from locations.storefinders.dominos_pizza_international import DominosPizzaInternationalSpider


class DominosPizzaKHSpider(DominosPizzaInternationalSpider):
    name = "dominos_pizza_kh"
    region_code = "KH"
    dpz_market = "CAMBODIA"
