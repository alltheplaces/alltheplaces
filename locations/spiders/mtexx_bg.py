from scrapy import Spider

from locations.items import Feature


class MtexxBGSpider(Spider):
    name = "mtexx_bg"
    item_attributes = {"brand": "M-texx", "brand_wikidata": "Q122947768"}
    allowed_domains = ["www.m-texx.com"]
    start_urls = ["https://m-texx.com/локации"]

    def parse(self, response):
        for locations in response.xpath('//div[@"data-ux"="GridCell"]'):
            for location in locations.xpath("//li"):
                properties = {
                    "name": location.xpath('.//span[@class="name"]/text()').get().rsplit("-")[0],
                    "lat": location.xpath(".//@data-lat").get().rsplit(",", 1)[0].rsplit(" ")[1],
                    "lon": location.xpath(".//@data-lng").get().rsplit(",", 1)[1],
                }
                yield Feature(**properties)
