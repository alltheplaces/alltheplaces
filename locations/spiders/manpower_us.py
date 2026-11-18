from locations.storefinders.manpower_sitecore import ManpowerSitecoreSpider


class ManpowerUSSpider(ManpowerSitecoreSpider):
    name = "manpower_us"
    start_urls = ["https://www.manpower.com/en/about-us/locations"]
