import re

from locations.hours import DAYS_EN, DAYS_PL
from locations.storefinders.adecco_sitecore import AdeccoSitecoreSpider


class AdeccoPLSpider(AdeccoSitecoreSpider):
    name = "adecco_pl"
    site_name = "AdeccoPL"
    language = "en"
    root_path_id = "03b1b48f-b6e3-4ddc-b1d9-14f975ac4015"
    locale = "en-pl"
    hours_kwargs = {"days": DAYS_EN | DAYS_PL}
    # Head office.
    excluded = re.compile(r"\bCentrala\b")
