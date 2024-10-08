from scrapy import Spider

from locations.items import Feature


class Hb1PharmacyPHSpider(Spider):
    name = "hb1_pharmacy_ph"
    item_attributes = {"brand_wikidata": "Q120350751"}
    start_urls = ["https://nccc.com.ph/business-unit/hb1-pharmacy/"]
    no_refs = True

    def parse(self, response, **kwargs):
        for location in response.xpath('//ul[@class="contact"]/parent::div/parent::div'):
            item = Feature()
            item["name"] = location.xpath(".//span/text()").get()
            item["addr_full"] = location.xpath('//li[@class="address"]/text()').get()
            item["phone"] = location.xpath('//li[@class="contact-number"]/text()').get()
            item["email"] = location.xpath('//li[@class="email"]/text()').get()

            yield item
