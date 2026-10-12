from locations.storefinders.manpower_sitecore import ManpowerSitecoreSpider


class ManpowerPLSpider(ManpowerSitecoreSpider):
    name = "manpower_pl"
    start_urls = ["https://www.manpower.pl/pl/o-nas/nasze-oddzialy"]
