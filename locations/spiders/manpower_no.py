from locations.hours import CLOSED_NO, DAYS_NO
from locations.storefinders.manpower_sitecore import ManpowerSitecoreSpider


class ManpowerNOSpider(ManpowerSitecoreSpider):
    name = "manpower_no"
    start_urls = ["https://www.manpower.no/nb/om-oss/vare-kontorer"]
    hours_kwargs = {"days": DAYS_NO, "closed": CLOSED_NO}
