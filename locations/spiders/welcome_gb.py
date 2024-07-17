from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class WelcomeGBSpider(SitemapSpider, StructuredDataSpider):
    name = "welcome_gb"
    item_attributes = {"brand": "Welcome", "brand_wikidata": "Q123004215"}
    sitemap_urls = ["https://stores.welcome-stores.co.uk/sitemap.xml"]
    sitemap_rules = [(r"/.+/.+/.+\.html$", "parse_sd")]
    wanted_types = ["GroceryStore"]
