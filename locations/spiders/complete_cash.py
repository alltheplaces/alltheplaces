from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class CompleteCashSpider(SitemapSpider, StructuredDataSpider):
    name = "complete_cash"
    item_attributes = {"brand": "Complete Cash", "brand_wikidata": "", "extras": Categories.SHOP_PAWNBROKER.value}
    allowed_domains = ["locations.completecash.net"]
    sitemap_urls = ["https://locations.completecash.net/sitemap.xml"]
    sitemap_rules = [("", "parse_sd")]
    wanted_types = ["Place"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["street_address"] = item["street_address"].replace(", null", "")
        yield item
