from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class AlliedIrishBanksIESpider(SitemapSpider, StructuredDataSpider):
    name = "allied_irish_banks_ie"
    item_attributes = {"brand": "AIB", "brand_wikidata": "Q1642179", "extras": Categories.BANK.value}
    sitemap_urls = ["https://branches.aib.ie/robots.txt"]
    sitemap_rules = [(r"https://branches.aib.ie/.+/.+/.+", "parse_sd")]
    wanted_types = ["BankOrCreditUnion"]
    drop_attributes = {"image"}
