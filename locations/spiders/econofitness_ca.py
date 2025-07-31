import scrapy
from scrapy.http import Response

from locations.items import Feature


class EconofitnessCASpider(scrapy.Spider):
    name = "econofitness_ca"
    item_attributes = {"brand": "Éconofitness", "brand_wikidata": "Q123073582"}
    start_urls = ["https://econofitness.ca/en/gym/"]

    def parse(self, response: Response, **kwargs):
        for location in response.xpath('//*[@data-js="location"]'):
            item = Feature()
            item["branch"] = location.xpath(".//h4/text()").get().removeprefix("Éconofitness ").removesuffix(" 24/7")
            item["lat"] = location.xpath("./@data-lat").get()
            item["lon"] = location.xpath("./@data-lng").get()
            item["ref"] = location.xpath("./@data-gym-id").get()
            item["addr_full"] = location.xpath('.//*[@class="address"]//span/text()').get()
            item["website"] = location.xpath('.//*[contains(@href,"/en/gym/")]/@href').get()
            yield item
