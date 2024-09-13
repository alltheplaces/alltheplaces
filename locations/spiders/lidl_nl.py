from locations.hours import DAYS_NL
from locations.spiders.lidl_at import LidlATSpider


class LidlNLSpider(LidlATSpider):
    name = "lidl_nl"

    dataset_id = "067b84e1e31f4f71974d1bfb6c412382"
    dataset_name = "Filialdaten-NL/Filialdaten-NL"
    api_key = "Ajsi91aW1OJ9ikqcOGadJ74W0D94pBKQ9Gha57tI6vXTTZZi1lwUuTXD2xDA-i7B"
    days = DAYS_NL
