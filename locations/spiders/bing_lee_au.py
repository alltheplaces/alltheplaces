from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class BingLeeAUSpider(SitemapSpider, StructuredDataSpider):
    name = "bing_lee_au"
    item_attributes = {"brand": "Bing Lee", "brand_wikidata": "Q4914136"}
    sitemap_urls = ["https://www.binglee.com.au/public/sitemap-locations.xml"]
    sitemap_rules = [(r"\/stores\/", "parse_sd")]
    wanted_types = ["ElectronicsStore"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
