import re

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class LouisVuittonSpider(SitemapSpider, StructuredDataSpider):
    name = "louis_vuitton"
    item_attributes = {"brand": "Louis Vuitton", "brand_wikidata": "Q191485", "name": "Louis Vuitton"}
    # This single sitemap (served off the US site) lists point-of-sale pages for stores in ~65 countries worldwide.
    sitemap_urls = ["https://us.louisvuitton.com/content/louisvuitton/sitemap/eng_US/sitemap-content.xml"]
    sitemap_rules = [(r"/point-of-sale/", "parse_sd")]
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}
    # Akamai blocks requests from data centre IPs with a 403 "Access Denied"; route through Zyte proxy.
    requires_proxy = True

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = re.sub(r"^Louis Vuitton\s*", "", item.pop("name"), flags=re.IGNORECASE).strip()

        apply_category(Categories.SHOP_CLOTHES, item)

        yield item
