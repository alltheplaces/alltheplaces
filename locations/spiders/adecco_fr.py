from locations.hours import CLOSED_EN, CLOSED_FR, DAYS_EN, DAYS_FR
from locations.storefinders.adecco_sitecore import AdeccoSitecoreSpider


class AdeccoFRSpider(AdeccoSitecoreSpider):
    name = "adecco_fr"
    site_name = "AdeccoFR"
    language = "fr-FR"
    root_path_id = "cfb5e9b3-b605-4c23-92c8-25eb759f3de5"
    locale = "fr-fr"
    hours_kwargs = {"days": DAYS_EN | DAYS_FR, "closed": CLOSED_EN + CLOSED_FR}
    # All ~960 entries on one page (~35s): pages from different origin servers don't line up.
    page_size = 1000
    custom_settings = {"DOWNLOAD_TIMEOUT": 60}
