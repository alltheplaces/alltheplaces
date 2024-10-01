from locations.storefinders.dominos_pizza_international import DominosPizzaInternationalSpider


class DominosPizzaHRSpider(DominosPizzaInternationalSpider):
    name = "dominos_pizza_hr"
    region_code = "HR"
    dpz_market = "CROATIA"
    search_radius = 1000000
