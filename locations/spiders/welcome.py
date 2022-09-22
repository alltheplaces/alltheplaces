from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class WelcomeGB(SitemapSpider, StructuredDataSpider):
    name = "welcome"
    item_attributes = {"brand": "Welcome"}
    sitemap_urls = ["https://stores.welcome-stores.co.uk/sitemap.xml"]
    sitemap_rules = [
        (
            "https:\/\/stores\.welcome-stores\.co\.uk\/[-\w]+\/[-\w]+\/[-\w]+\.html$",
            "parse_sd",
        )
    ]
    wanted_types = ["GroceryStore"]
