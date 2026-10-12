from locations.hours import CLOSED_SE, DAYS_SE, NAMED_DAY_RANGES_SE
from locations.storefinders.manpower_sitecore import ManpowerSitecoreSpider


class ManpowerSESpider(ManpowerSitecoreSpider):
    name = "manpower_se"
    start_urls = ["https://www.manpower.se/sv/om-oss/vara-kontor"]
    hours_kwargs = {"days": DAYS_SE, "named_day_ranges": NAMED_DAY_RANGES_SE, "closed": CLOSED_SE}
