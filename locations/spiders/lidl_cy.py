from locations.hours import DAYS_ES
from locations.spiders.lidl_at import LidlATSpider


class LidlCYSpider(LidlATSpider):
    name = "lidl_cy"

    dataset_id = "cb33ea3051cb48c29ed0bf1022885485"
    dataset_name = "Filialdaten-CY/Filialdaten-CY"
    api_key = "AmX2Tc6F7G8vXa586XIzoFwbnhI3ViP6BvDenldmtaxLB1uELgvbADtwRxdwEZTS"
    days = DAYS_ES
