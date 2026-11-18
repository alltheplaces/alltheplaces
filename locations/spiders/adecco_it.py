import re

from locations.hours import CLOSED_EN, CLOSED_IT, DAYS_EN, DAYS_IT, DELIMITERS_IT
from locations.storefinders.adecco_sitecore import AdeccoSitecoreSpider


class AdeccoITSpider(AdeccoSitecoreSpider):
    name = "adecco_it"
    site_name = "AdeccoIT"
    language = "it-IT"
    root_path_id = "0cde1891-f3bc-472d-be97-80762d856627"
    locale = "it-it"
    hours_kwargs = {"days": DAYS_EN | DAYS_IT, "closed": CLOSED_EN + CLOSED_IT, "delimiters": DELIMITERS_IT}
    # Nearly all branches are just named "Adecco".
    branch_from_city = True
    # Head office.
    excluded = re.compile(r"^The Adecco Group\b")
