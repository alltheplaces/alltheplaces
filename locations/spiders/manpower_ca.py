from locations.storefinders.manpower_sitecore import ManpowerSitecoreSpider


class ManpowerCASpider(ManpowerSitecoreSpider):
    name = "manpower_ca"
    start_urls = ["https://www.manpower.ca/en/about-us/locations"]
    # robots.txt only allows a list of named search engine and SEO crawlers.
    custom_settings = {"ROBOTSTXT_OBEY": False}
