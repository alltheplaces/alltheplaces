import scrapy
from locations.categories import Categories, apply_category

from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser


class FnbUSSpider(scrapy.spiders.SitemapSpider):
    name = "fnb_us"
    item_attributes = {"brand": "First National Bank", "brand_wikidata": "Q5426765"}
    allowed_domains = ["fnb-online.com"]
    sitemap_urls = [
        "https://locations.fnb-online.com/robots.txt",
    ]
    sitemap_rules = [
        (r"^https://locations\.fnb-online\.com/[^/]+/[^/]+/[^/]+$", "parse"),
    ]

    def parse(self, response):
        for city in response.css('[itemprop="address"] .Address-city'):
            city.root.set("itemprop", "addressLocality")
        MicrodataParser.convert_to_json_ld(response)
        item = LinkedDataParser.parse(response, "BankOrCreditUnion")
        item["country"] = "US"
        apply_category(Categories.BANK, item)
        # TODO: more data at:
        # https://www.fnb-online.com/atm-branch-locator?=&query=&facetFilters=%7B%7D&filters=%7B%7D&referrerPageUrl=https%3A%2F%2Fwww.fnb-online.com%2F&verticalUrl=branches.html
        yield item
