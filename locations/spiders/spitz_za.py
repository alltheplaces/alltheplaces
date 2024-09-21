from scrapy.http import Request
from scrapy.spiders import Spider

from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class SpitzZASpider(Spider):
    name = "spitz_za"
    allowed_domains = ["www.spitz.co.za"]
    start_urls = ["https://www.spitz.co.za/stores"]
    item_attributes = {
        "brand": "Spitz",
        "brand_wikidata": "Q116620967",
    }

    def parse(self, response):
        for url in response.xpath('.//a[@class="directions"]/@href').getall():
            yield Request(url=url, callback=self.parse_store)
        for url in response.xpath('.//a[@class="action  next"]/@href').getall():
            yield Request(url=url, callback=self.parse)

    def parse_store(self, response):
        item = Feature()
        item["ref"] = response.url
        item["website"] = response.url
        item["branch"] = response.xpath('.//h1[@class="page-title"]/span/text()').get()
        item["addr_full"] = clean_address(response.xpath('.//div[@class="shop-contact-address"]/text()').get())
        item["phone"] = response.xpath('.//div[contains(@class,"phone-number")]/div/text()').get()
        if item["phone"] is not None and "/" in item["phone"] and len(item["phone"].split("/")[1]) == 1:
            split = item["phone"].split("/")
            item["phone"] = split[0] + "; " + split[0][:-1] + split[1]
        extract_google_position(item, response)

        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(
            response.xpath('string(.//div[@class="shop-opening-times"])').get()
        )

        yield item
