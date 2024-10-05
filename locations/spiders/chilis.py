import scrapy

from locations.linked_data_parser import LinkedDataParser


class ChilisSpider(scrapy.Spider):
    name = "chilis"
    item_attributes = {"brand": "Chili's", "brand_wikidata": "Q1072948"}
    allowed_domains = ["chilis.com"]
    download_delay = 0.5
    start_urls = ("https://www.chilis.com/locations/us/all",)

    def parse_store(self, response):
        item = LinkedDataParser.parse(response, "Restaurant")
        item["ref"] = data["branchCode"]
        yield item

    def parse_city(self, response):
        urls = response.xpath('//a[text()="Details"]/@href').extract()
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_store)

    def parse(self, response):
        urls = response.xpath('//div[contains(@class, "city-locations")]//a[@class="city-link"]/@href').extract()
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_city)
