import scrapy

from locations.categories import Categories
from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser


class FifthThirdBankSpider(scrapy.spiders.SitemapSpider):
    name = "fifth_third_bank"
    item_attributes = {"brand": "Fifth Third Bank", "brand_wikidata": "Q1411810", "extras": Categories.BANK.value}
    allowed_domains = [
        "53.com",
    ]
    sitemap_urls = [
        "https://locations.53.com/robots.txt",
    ]

    def parse(self, response):
        MicrodataParser.convert_to_json_ld(response.selector)
        for obj in LinkedDataParser.iter_linked_data(response):
            # Page includes nearby locations; find the one that's the subject
            # of this page. We're going to crawl all the pages anyway, so take
            # the one that also includes the yext itemid.
            if obj["@type"] == "BankOrCreditUnion" and "@id" in obj:
                break
        else:
            return
        if obj:
            item = LinkedDataParser.parse_ld(obj)
            yield item
