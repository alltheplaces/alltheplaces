from locations.storefinders.dominos_pizza_international import DominosPizzaInternationalSpider


class DominosPizzaCHSpider(DominosPizzaInternationalSpider):
    name = "dominos_pizza_ch"
    region_code = "CH"
    dpz_market = "SWITZERLAND"
