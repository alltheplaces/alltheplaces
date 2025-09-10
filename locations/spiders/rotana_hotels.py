from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class RotanaHotelsSpider(SitemapSpider, StructuredDataSpider):
    name = "rotana_hotels"
    item_attributes = {"brand": "Rotana Hotels", "brand_wikidata": "Q7370229"}
    sitemap_urls = ["https://www.rotana.com/sitemap.xml"]
    sitemap_rules = [(r"^https://www.rotana.com/rotanahotelandresorts/\w+/\w+/\w+$", "parse_sd")]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.HOTEL, item)
        item["branch"] = item.pop("name")
        yield item
