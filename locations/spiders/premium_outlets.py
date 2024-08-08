import html
import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class PremiumOutletsSpider(SitemapSpider, StructuredDataSpider):
    name = "premium_outlets"
    item_attributes = {"brand": "Premium Outlets"}
    sitemap_urls = ["https://www.premiumoutlets.com/sitemap-po.xml"]
    sitemap_rules = [(r"/outlet/[^/]+/about$", "parse")]
    wanted_types = ["ShoppingCenter"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = html.unescape(item["name"])

        if m := re.search(r"\"Longitude\":(-?\d+\.\d+),\"Latitude\":(-?\d+\.\d+),", response.text):
            item["lon"], item["lat"] = m.groups()

        if m := re.search(r"\"CountryCode\":\"(\w\w\w)\"", response.text):
            item["country"] = m.group(1)

        apply_category(Categories.SHOP_MALL, item)

        yield item
