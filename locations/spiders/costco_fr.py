import re

from locations.hours import CLOSED_FR, DAYS_FR, DELIMITERS_FR, OpeningHours
from locations.spiders.costco_au import CostcoAUSpider


class CostcoFRSpider(CostcoAUSpider):
    name = "costco_fr"
    allowed_domains = ["www.costco.fr"]
    start_urls = ["https://www.costco.fr/store-finder/search?q="]
    day_labels = DAYS_FR
    delimiters = DELIMITERS_FR
    closed_labels = CLOSED_FR

    def parse_hours_string(self, hours_string: str) -> OpeningHours:
        hours_string = re.sub(
            r"(?<=\d)h(?!\d)",
            ":00",
            re.sub(
                r"(?<=\d)h(?=\d)",
                ":",
                hours_string.replace(".:", ":")
                .replace("station service", "")
                .replace("Tous les dimanches", "Dimanche")
                .replace("00:00 - 00:00", "Fermée"),
            ),
        )
        return super().parse_hours_string(hours_string)
