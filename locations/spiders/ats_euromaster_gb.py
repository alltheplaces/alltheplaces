import re

import scrapy

from locations.items import Feature


class AtsEuromasterGBSpider(scrapy.Spider):
    name = "ats_euromaster_gb"
    start_urls = ["https://www.atseuromaster.co.uk/centres"]
    item_attributes = {"brand": "ATS Euromaster", "brand_wikidata": "Q4654920"}

    def parse(self, response):
        regions = response.xpath('//*[@class="list-group-item border-0 p-0"]//@href').getall()
        for region in regions:
            yield scrapy.Request(url=region, callback=self.parse_region)

    def parse_region(self, response):
        cities = response.xpath('//*[@class="list-province w-100"]//li//@href').getall()
        for shop in cities:
            yield scrapy.Request(url=shop, callback=self.parse_shop)

    def parse_shop(self, response):
        item = Feature()
        item["ref"] = response.xpath('//*[@class="model-dealer-infos"]/@data-id').get()
        item["branch"] = response.xpath('//*[@class="model-dealer-infos"]/@data-name').get()
        item["street_address"] = response.xpath('//*[@class="model-dealer-infos"]/@data-address').get()
        item["postcode"] = response.xpath('//*[@class="model-dealer-infos"]/@data-postcode').get()
        item["city"] = response.xpath('//*[@class="model-dealer-infos"]/@data-city').get()
        item["state"] = response.xpath('//*[@class="model-dealer-infos"]/@data-region').get()
        item["extras"]["ref:google:place_id"] = response.xpath(
            '//*[@class="model-dealer-infos"]/@data-google-map-place-id'
        ).get()
        item["lat"], item["lon"] = re.search(r"mapInit\('(.*)', '(.*)', true", response.text).groups()
        yield item
