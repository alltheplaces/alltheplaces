from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class BankOfScotlandGB(SitemapSpider, StructuredDataSpider):
    name = "bank_of_scotland_gb"
    item_attributes = {
        "brand": "Bank of Scotland",
        "brand_wikidata": "Q627381",
        "extras": {"amenity": "bank"},
    }
    sitemap_urls = ["https://branches.bankofscotland.co.uk/sitemap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/branches\.bankofscotland\.co\.uk\/[-\w]+\/([-\/'\w]+)$",
            "parse_sd",
        )
    ]
    wanted_types = ["BankOrCreditUnion"]
