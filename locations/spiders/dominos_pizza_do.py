from locations.hours import DAYS_ES
from locations.storefinders.dominos_pizza_international import DominosPizzaInternationalSpider


class DominosPizzaDOSpider(DominosPizzaInternationalSpider):
    name = "dominos_pizza_do"
    region_code = "DO"
    dpz_market = "DOMINICAN_REPUBLIC"
    domain = "order.golo01.dominos.com"
    dpz_language = "es"
    days = DAYS_ES
