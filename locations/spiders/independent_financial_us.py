from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class IndependentFinancialUSSpider(SitemapSpider, StructuredDataSpider):
    name = "independent_financial_us"
    item_attributes = {"brand": "Independent Financial", "brand_wikidata": "Q6016398"}
    sitemap_urls = ["https://locations.ifinancial.com/sitemap.xml"]
    sitemap_rules = [(r"https://locations.ifinancial.com/\w+/[a-z-0-9]+/[a-z-0-9]+", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        if "/atm" in response.url:
            apply_category(Categories.ATM, item)
        else:
            apply_category(Categories.BANK, item)
        yield item
