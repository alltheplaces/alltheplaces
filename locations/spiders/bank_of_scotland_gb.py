from locations.structured_data_spider import StructuredDataSpider

from scrapy.spiders import SitemapSpider


class BankOfScotlandGB(SitemapSpider, StructuredDataSpider):
    name = "bank_of_scotland_gb"
    item_attributes = {"brand": "Bank of Scotland", "brand_wikidata": "Q627381"}
    sitemap_urls = ["https://branches.bankofscotland.co.uk/sitemap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/branches\.bankofscotland\.co\.uk\/[-\w]+\/([-\/'\w]+)$",
            "parse_sd",
        )
    ]
    wanted_types = ["BankOrCreditUnion"]
