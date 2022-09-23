from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class LloydsBankGB(SitemapSpider, StructuredDataSpider):
    name = "lloyds_bank_gb"
    item_attributes = {"brand": "Lloyds Bank", "brand_wikidata": "Q1152847"}
    sitemap_urls = ["https://branches.lloydsbank.com/sitemap.xml"]
    sitemap_rules = [
        (r"https:\/\/branches\.lloydsbank\.com\/[-\w]+\/[-\/'\w]+$", "parse_sd")
    ]
    wanted_types = ["BankOrCreditUnion"]

    def sitemap_filter(self, entries):
        for entry in entries:
            if not "event" in entry["loc"]:
                yield entry
