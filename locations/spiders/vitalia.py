from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.items import Feature


class VitaliaSpider(CrawlSpider):
    name = "vitalia"
    item_attributes = {"brand": "Vitalia Reformhaus", "brand_wikidata": "Q2528558"}
    allowed_domains = ["www.vitalia-reformhaus.de"]
    start_urls = ["https://www.vitalia-reformhaus.de/marktfinder"]
    rules = [
        Rule(
            LinkExtractor(allow=".*/marktfinder/vitalia.*"),
            callback="parse",
            follow=False,
        )
    ]

    def parse(self, response):
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["city"] = response.xpath('//span[contains(., "Stadt:")]/following-sibling::span/text()').get()
        item["street_address"] = response.xpath(
            '//span[contains(., "Anschrift:")]/following-sibling::span/text()'
        ).get()
        item["postcode"] = response.xpath('//span[contains(., "PLZ:")]/following-sibling::span/text()').get()
        item["phone"] = response.xpath('//*[contains(@href,"tel:")]/@href').get().replace("tel:", "")
        yield item
