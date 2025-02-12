from locations.hours import DAYS_ES
from locations.storefinders.dominos_pizza_international import DominosPizzaInternationalSpider


class DominosPizzaPESpider(DominosPizzaInternationalSpider):
    name = "dominos_pizza_pe"
    region_code = "PE"
    dpz_market = "PERU"
    domain = "order.golo01.dominos.com"
    dpz_language = "es"
    days = DAYS_ES
