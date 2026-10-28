import re

from locations.hours import CLOSED_EN, CLOSED_ES, DAYS_EN, DAYS_ES, DELIMITERS_ES
from locations.storefinders.adecco_sitecore import AdeccoSitecoreSpider


class AdeccoESSpider(AdeccoSitecoreSpider):
    name = "adecco_es"
    site_name = "AdeccoES"
    language = "es-ES"
    root_path_id = "02bf2dcf-01c8-48fb-a077-2e7c4bccc5e9"
    locale = "es-es"
    hours_kwargs = {"days": DAYS_EN | DAYS_ES, "closed": CLOSED_EN + CLOSED_ES, "delimiters": DELIMITERS_ES}
    # Branch names are business lines ("Adecco Staffing", "Adecco Outsourcing").
    branch_from_city = True
    # Head office, and offices of Eurocen, another group brand.
    excluded = re.compile(r"^(The Adecco Group\b|Eurocen$)")
