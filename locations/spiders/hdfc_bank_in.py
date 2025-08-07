from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class HdfcBankINSpider(SitemapSpider, StructuredDataSpider):
    name = "hdfc_bank_in"
    item_attributes = {"brand": "HDFC Bank", "brand_wikidata": "Q631047"}
    sitemap_urls = [
        "https://near-me.hdfcbank.com/branch-atm-locator/files/enterprise/sitemap/google/5280/locations.xml"
    ]
    sitemap_rules = [
        (r"https://near-me.hdfcbank.com/branch-atm-locator/.*/Home$", "parse_sd"),
    ]
    time_format = "%I:%M %p"
    requires_proxy = "IN"

    def post_process_item(self, item, response, ld_data, **kwargs):
        item.pop("phone")
        if "ATM" in item["name"]:
            apply_category(Categories.ATM, item)
        else:
            apply_category(Categories.BANK, item)
        yield item
