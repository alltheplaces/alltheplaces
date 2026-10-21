from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider


class GoodyearUSSpider(SitemapSpider, StructuredDataSpider, PlaywrightSpider):
    name = "goodyear_us"
    item_attributes = {"brand": "Goodyear", "brand_wikidata": "Q620875"}
    sitemap_urls = ["https://www.goodyear.com/en-us/retail-locations-sitemap.xml"]
    sitemap_rules = [(r"^https://www.goodyear.com/en-us/shops/[^/]+/[^/]+/Goodyear-.+$", "parse_sd")]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def post_process_item(self, item, response, ld_data):
        item["branch"] = item.pop("name").replace("Goodyear Auto Service - ", "")
        apply_category(Categories.SHOP_TYRES, item)
        yield item
