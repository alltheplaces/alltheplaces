from locations.hours import DAYS_ES
from locations.storefinders.dominos_pizza_international import DominosPizzaInternationalSpider


class DominosPizzaMXSpider(DominosPizzaInternationalSpider):
    name = "dominos_pizza_mx"
    region_code = "MX"
    dpz_market = "MEXICO"
    domain = "order.golo01.dominos.com"
    dpz_language = "es"
    days = DAYS_ES
