from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class TccUSSpider(SitemapSpider, StructuredDataSpider):
    name = "tcc_us"
    item_attributes = {
        "brand": "Verizon",
        "brand_wikidata": "Q919641",
        "operator": "The Cellular Connection",
        "operator_wikidata": "Q121336519",
    }
    drop_attributes = {"image"}
    sitemap_urls = ["https://locations.tccrocks.com/sitemap.xml"]
    sitemap_rules = [(r"https://locations.tccrocks.com/\w\w/.+/.+\.html", "parse_sd")]
    wanted_types = ["MobilePhoneStore"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        apply_category(Categories.SHOP_MOBILE_PHONE, item)
        yield item
