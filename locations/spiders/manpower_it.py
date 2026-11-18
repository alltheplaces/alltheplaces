from locations.storefinders.manpower_sitecore import ManpowerSitecoreSpider


class ManpowerITSpider(ManpowerSitecoreSpider):
    name = "manpower_it"
    start_urls = ["https://www.manpower.it/it/cerca-filiale"]
