from locations.hours import DAYS_FR
from locations.spiders.costco_au import CostcoAUSpider


class CostcoFRSpider(CostcoAUSpider):
    name = "costco_fr"
    allowed_domains = ["www.costco.fr"]
    stores_url = (
        "https://www.costco.fr/rest/v2/france/stores?fields=FULL&radius=3000000&returnAllStores=true&pageSize=999"
    )
    days = DAYS_FR
    time_format = "%H:%M"
