import re

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class FamousFootwearSpider(SitemapSpider, StructuredDataSpider):
    name = "famous_footwear"
    item_attributes = {"brand": "Famous Footwear", "brand_wikidata": "Q5433457"}
    sitemap_urls = ["https://ecomprdsharedstorage.blob.core.windows.net/sitemaps/20000/stores-sitemap.xml"]
    sitemap_rules = [("", "parse_sd")]
    wanted_types = ["Store"]
    user_agent = BROWSER_DEFAULT
    custom_settings = {"ROBOTSTXT_OBEY": False}
    requires_proxy = True

    def inspect_item(self, item, response):
        matches = re.search(r'location: \["(.*)", "(.*)"\],', response.text)
        item["lat"], item["lon"] = matches[1], matches[2]
        yield item
