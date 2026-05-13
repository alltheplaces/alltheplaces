from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class HomeDepotSpider(SitemapSpider, StructuredDataSpider):
    name = "home_depot"
    item_attributes = {"brand": "The Home Depot", "brand_wikidata": "Q864407"}
    sitemap_urls = ["https://www.homedepot.com/sitemap/main.xml"]
    sitemap_rules = [(r"https://www.homedepot.com/l/[^/]+/[^/]+/[^/]+/\d+/\d+$", "parse_sd")]
    requires_proxy = True
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
