from locations.hours import CLOSED_DE, CLOSED_EN, DAYS_DE, DAYS_EN, DELIMITERS_DE
from locations.storefinders.adecco_sitecore import AdeccoSitecoreSpider


class AdeccoATSpider(AdeccoSitecoreSpider):
    name = "adecco_at"
    site_name = "AdeccoAT"
    language = "de-AT"
    root_path_id = "f843de30-aa52-4bf7-ab75-99ddd56272a1"
    locale = "de-at"
    hours_kwargs = {"days": DAYS_EN | DAYS_DE, "closed": CLOSED_EN + CLOSED_DE, "delimiters": DELIMITERS_DE}
    postcode_in_address_extension = True
