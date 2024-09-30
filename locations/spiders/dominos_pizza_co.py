from locations.hours import DAYS_ES
from locations.storefinders.dominos_pizza_international import DominosPizzaInternationalSpider


class DominosPizzaCOSpider(DominosPizzaInternationalSpider):
    name = "dominos_pizza_co"
    region_code = "CO"
    dpz_market = "COLOMBIA"
    domain = "order.golo01.dominos.com"
    dpz_language = "es"
    days = DAYS_ES
