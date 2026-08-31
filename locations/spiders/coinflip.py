from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class CoinflipSpider(SitemapSpider, StructuredDataSpider):
    name = "coinflip"
    item_attributes = {"brand": "CoinFlip", "brand_wikidata": "Q109850256"}
    sitemap_urls = ["https://coinflip.tech/locations-sitemap.xml"]
    sitemap_rules = [(r"https://locations.coinflip.tech/[^/]+/[^/]+/[^/]+/[^/]+$", "parse_sd")]
    wanted_types = ["AutomatedTeller"]
    custom_settings = {"ROBOTSTXT_OBEY": False, "CONCURRENT_REQUESTS": 1, "USER_AGENT": BROWSER_DEFAULT}
