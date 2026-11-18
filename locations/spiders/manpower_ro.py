from locations.storefinders.manpower_sitecore import ManpowerSitecoreSpider


class ManpowerROSpider(ManpowerSitecoreSpider):
    name = "manpower_ro"
    start_urls = ["https://www.manpower.ro/ro/locations"]
    # robots.txt only allows a list of named search engine and SEO crawlers.
    custom_settings = {"ROBOTSTXT_OBEY": False}
