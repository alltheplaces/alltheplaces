from locations.hours import CLOSED_DE, CLOSED_EN, DAYS_DE, DAYS_EN, DELIMITERS_DE
from locations.storefinders.adecco_sitecore import AdeccoSitecoreSpider


class AdeccoCHSpider(AdeccoSitecoreSpider):
    name = "adecco_ch"
    site_name = "AdeccoCH"
    language = "de-CH"
    root_path_id = "cd0eae80-4368-4c56-b6de-1ff06ff1b2f6"
    locale = "de-ch"
    hours_kwargs = {"days": DAYS_EN | DAYS_DE, "closed": CLOSED_EN + CLOSED_DE, "delimiters": DELIMITERS_DE}
