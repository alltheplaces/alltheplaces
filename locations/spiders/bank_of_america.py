import html

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class BankOfAmericaSpider(SitemapSpider, StructuredDataSpider):
    name = "bank_of_america"
    item_attributes = {"brand": "Bank of America", "brand_wikidata": "Q487907"}
    sitemap_urls = ["https://locators.bankofamerica.com/robots.txt"]
    sitemap_rules = [(r"com/\w\w/\w+/[-\w]+\.html$", "parse_sd")]
    wanted_types = ["FinancialService", "AutomatedTeller"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = html.unescape(item["name"])

        if ld_data["@type"] == "FinancialService":
            apply_category(Categories.BANK, item)
        elif ld_data["@type"] == "AutomatedTeller":
            apply_category(Categories.ATM, item)

        yield item
