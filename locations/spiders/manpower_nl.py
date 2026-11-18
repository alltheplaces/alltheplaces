from locations.hours import CLOSED_NL, DAYS_NL
from locations.storefinders.manpower_sitecore import ManpowerSitecoreSpider


class ManpowerNLSpider(ManpowerSitecoreSpider):
    name = "manpower_nl"
    start_urls = ["https://www.manpower.nl/nl/over-manpower/vestigingen"]
    hours_kwargs = {"days": DAYS_NL | {"Vrij": "Fr"}, "closed": CLOSED_NL}
