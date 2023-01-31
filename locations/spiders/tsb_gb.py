from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class TSBGB(SitemapSpider, StructuredDataSpider):
    name = "tsb_gb"
    item_attributes = {
        "brand": "TSB",
        "brand_wikidata": "Q7671560",
        "extras": Categories.BANK.value,
    }
    sitemap_urls = ["https://branches.tsb.co.uk/sitemap.xml"]
    sitemap_rules = [(r"https:\/\/branches\.tsb\.co\.uk\/[-\w]+\/[-\/\w]+\.html$", "parse_sd")]
    wanted_types = ["BankOrCreditUnion", "FinancialService"]
