from locations.hours import DAYS_ES
from locations.storefinders.dominos_pizza_international import DominosPizzaInternationalSpider


class DominosPizzaUYSpider(DominosPizzaInternationalSpider):
    name = "dominos_pizza_uy"
    region_code = "UY"
    dpz_market = "URUGUAY"
    domain = "order.golo01.dominos.com"
    dpz_language = "es"
    days = DAYS_ES
