from locations.hours import CLOSED_DE, CLOSED_EN, DAYS_DE, DAYS_EN, DELIMITERS_DE
from locations.storefinders.adecco_sitecore import AdeccoSitecoreSpider


class AdeccoDESpider(AdeccoSitecoreSpider):
    name = "adecco_de"
    site_name = "AdeccoDE"
    language = "de-DE"
    root_path_id = "fc78aa73-6665-404d-b5fb-8ebe2e9993ff"
    locale = "de-de"
    hours_kwargs = {"days": DAYS_EN | DAYS_DE, "closed": CLOSED_EN + CLOSED_DE, "delimiters": DELIMITERS_DE}

    def pre_process_schedules(self, hours: str) -> str:
        # "Mo-Do 9:00-12:00 und 13:00-16:00 Uhr"
        return hours.replace(" und ", ", ")
