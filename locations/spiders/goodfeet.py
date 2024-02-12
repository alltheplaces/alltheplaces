from scrapy.spiders import SitemapSpider

from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class GoodfeetSpider(SitemapSpider, StructuredDataSpider):
    name = "goodfeet"
    item_attributes = {"brand": "Good Feet"}
    sitemap_urls = ["https://www.goodfeet.com/sitemap.xml"]
    sitemap_rules = [(r"/locations/(.*)$", "parse_sd")]
    # wanted_types = ["Store"]
    # is_playwright_spider = True
    # custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS
