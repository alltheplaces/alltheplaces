from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class JohnLewisSpider(SitemapSpider, StructuredDataSpider):
    name = "john_lewis"
    item_attributes = {"brand": "John Lewis", "brand_wikidata": "Q1918981"}
    sitemap_urls = ["https://www.johnlewis.com/shops-services.xml"]
    sitemap_rules = [("/our-shops/", "parse_sd")]

    custom_settings = {"REDIRECT_ENABLED": False}
    user_agent = BROWSER_DEFAULT
