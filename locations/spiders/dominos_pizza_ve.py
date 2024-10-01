from locations.hours import DAYS_ES
from locations.storefinders.dominos_pizza_international import DominosPizzaInternationalSpider


class DominosPizzaVESpider(DominosPizzaInternationalSpider):
    name = "dominos_pizza_ve"
    region_code = "VE"
    dpz_market = "VENEZUELA"
    domain = "order.golo01.dominos.com"
    dpz_language = "es"
    days = DAYS_ES
