import scrapy

from locations.items import Feature
from locations.spiders.mcdonalds import McdonaldsSpider


class McdonaldsTHSpider(scrapy.Spider):
    name = "mcdonalds_th"
    item_attributes = McdonaldsSpider.item_attributes
    start_urls = ["https://www.mcdonalds.co.th/storeLocations"]

    def parse(self, response):
        for s in response.xpath("//a[@data-lat]"):
            item = Feature()
            item["name"] = s.xpath('div[@class="name"]/text()').get()
            item["website"] = item["ref"] = s.xpath("@href").get()
            item["lat"] = s.xpath("@data-lat").get()
            item["lon"] = s.xpath("@data-lng").get()
            item["addr_full"] = s.xpath('div[@class="address"]/text()').get()
            yield item
