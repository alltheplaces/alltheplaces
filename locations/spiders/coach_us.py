from scrapy.spiders import SitemapSpider

from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class CoachUSSpider(SitemapSpider, StructuredDataSpider):
    name = "coach_us"
    item_attributes = {"brand": "Coach", "brand_wikidata": "Q727697"}
    sitemap_urls = ["https://www.coach.com/stores/sitemap.xml"]
    sitemap_rules = [(r"https://www.coach.com/stores/[^/]+/[^/]+/[^/]+$", "parse_sd")]
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"USER_AGENT": BROWSER_DEFAULT}
