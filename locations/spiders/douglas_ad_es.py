from locations.hours import DAYS_ES
from locations.spiders.douglas_de import DouglasDESpider


class DouglasADESSpider(DouglasDESpider):
    name = "douglas_ad_es"
    allowed_domains = ["www.douglas.es"]
    start_urls = ["https://www.douglas.es/api/v2/stores?accuracy=0&currentPage=0&fields=FULL&pageSize=10000&sort=asc"]
    days = DAYS_ES

    def pre_process_data(self, feature: dict) -> None:
        # Some stores (e.g. Murcia) have no "url" or "openingHours"
        if not feature.get("openingHours"):
            feature["openingHours"] = {"weekDayOpeningList": []}
        if not (url := feature.get("url")):
            feature["url"] = ""

        super().pre_process_data(feature)
        if not url:
            feature.pop("website")
