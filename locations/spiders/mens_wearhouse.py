from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class MensWearhouseSpider(SitemapSpider, StructuredDataSpider):
    name = "mens_wearhouse"
    item_attributes = {"brand": "Men's Wearhouse", "brand_wikidata": "Q57405513"}
    sitemap_urls = [
        "https://www.menswearhouse.com/sitemap-store-locator.xml",
    ]
    sitemap_rules = [(r"/store-locator/[0-9]+", "parse_sd")]
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}
