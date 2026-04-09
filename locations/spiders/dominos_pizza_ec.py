from locations.hours import DAYS_ES
from locations.storefinders.dominos_pizza_international import DominosPizzaInternationalSpider


class DominosPizzaECSpider(DominosPizzaInternationalSpider):
    name = "dominos_pizza_ec"
    region_code = "EC"
    dpz_market = "ECUADOR"
    domain = "order.golo04.dominos.com"
    dpz_language = "es"
    days = DAYS_ES
