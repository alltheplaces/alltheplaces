from locations.storefinders.manpower_sitecore import ManpowerSitecoreSpider


class ManpowerPTSpider(ManpowerSitecoreSpider):
    name = "manpower_pt"
    start_urls = ["https://www.manpower.pt/pt/locations"]
    # robots.txt only allows a list of named search engine and SEO crawlers.
    custom_settings = {"ROBOTSTXT_OBEY": False}
