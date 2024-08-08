import scrapy

from locations.categories import Categories, apply_category
from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser


class NorthwestBankSpider(scrapy.spiders.SitemapSpider):
    name = "northwest_bank"
    item_attributes = {"brand": "Northwest Bank", "brand_wikidata": "Q7060191"}
    allowed_domains = ["northwest.bank"]
    sitemap_urls = ["https://locations.northwest.bank/robots.txt"]

    def parse(self, response):
        # Contains branch hours and and drive thru hours undifferentiated;
        # inject a scope to keep them from collapsing
        for div in response.xpath('(//h2/..)[.//*[@itemprop="openingHours"]]'):
            div.root.set("itemscope")
            div.root.set("itemprop", "department")
            div.root.set("itemtype", "http://schema.org/Department")
            h2 = div.xpath("./h2")[0]
            h2.root.set("itemprop", "name")
        for city in response.css('[itemprop="address"] .Address-city'):
            city.root.set("itemprop", "addressLocality")
        MicrodataParser.convert_to_json_ld(response.selector)
        item = LinkedDataParser.parse(response, "BankOrCreditUnion")
        if item:
            apply_category(Categories.BANK, item)
        yield item
