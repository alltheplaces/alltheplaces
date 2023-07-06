from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class CostcoSpider(SitemapSpider, StructuredDataSpider):
    name = "costco"
    item_attributes = {
        "brand": "Costco",
        "brand_wikidata": "Q715583",
        "extras": Categories.SHOP_WHOLESALE.value,
    }
    allowed_domains = ["www.costco.com"]
    user_agent = BROWSER_DEFAULT
    custom_settings = {"ROBOTSTXT_OBEY": False}
    sitemap_urls = ["https://www.costco.com/sitemap_lw_index.xml"]
    sitemap_follow = ["lw_l"]
    sitemap_rules = [("/warehouse-locations/", "parse_sd")]
