from locations.storefinders.dominos_pizza_international import DominosPizzaInternationalSpider


class DominosPizzaKESpider(DominosPizzaInternationalSpider):
    name = "dominos_pizza_ke"
    region_code = "KE"
    dpz_market = "KENYA"
