from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class AlliedIrishBanksIESpider(SitemapSpider, StructuredDataSpider):
    name = "allied_irish_banks_ie"
    item_attributes = {"brand": "AIB", "brand_wikidata": "Q1642179"}
    sitemap_urls = ["https://branches.aib.ie/robots.txt"]
    sitemap_rules = [(r"https://branches.aib.ie/.+/.+/.+", "parse_sd")]
    wanted_types = ["BankOrCreditUnion"]
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        apply_category(Categories.BANK, item)
        yield item
