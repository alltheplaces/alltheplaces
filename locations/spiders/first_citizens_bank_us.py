from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class FirstCitizensBankUSSpider(SitemapSpider, StructuredDataSpider):
    name = "first_citizens_bank_us"
    item_attributes = {"brand": "First Citizens Bank", "brand_wikidata": "Q5452734"}
    sitemap_urls = ["https://locations.firstcitizens.com/robots.txt"]
    wanted_types = ["FinancialService"]
    sitemap_rules = [(r"https://locations.firstcitizens.com/.+?/.+?/.+", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if "atm" in response.url:
            apply_category(Categories.ATM, item)
        else:
            apply_category(Categories.BANK, item)
        yield item
