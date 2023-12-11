from json import loads

from scrapy import Spider

from locations.hours import OpeningHours
from locations.items import Feature


class SobeysCASpider(Spider):
    name = "sobeys_ca"
    item_attributes = {"brand": "Sobeys", "brand_wikidata": "Q1143340"}
    allowed_domains = ["www.sobeys.com"]
    start_urls = ["https://www.sobeys.com/store-locator/"]

    def parse(self, response):
        for store in response.xpath('//div[@class="store-result "]'):
            properties = {
                "ref": store.xpath(".//@data-id").get(),
                "name": store.xpath('.//span[@class="name"]/text()').get(),
                "lat": store.xpath(".//@data-lat").get(),
                "lon": store.xpath(".//@data-lng").get(),
                "street_address": store.xpath('.//span[@class="location_address_address_1"]/text()').get(),
                "city": store.xpath('.//span[@class="city"]/text()').get(),
                "state": store.xpath('.//span[@class="province"]/text()').get().upper(),
                "postcode": store.xpath('.//span[@class="postal_code"]/text()').get(),
                "phone": store.xpath('.//span[@class="phone"]/a/text()').get(),
                "website": store.xpath('.//a[@class="store-title"]/@href').get(),
                "opening_hours": OpeningHours(),
            }
            hours_json = loads(store.xpath(".//@data-hours").get())
            hours_string = " ".join(
                ["{}: {}".format(day_name, hours_range) for day_name, hours_range in hours_json.items()]
            )
            properties["opening_hours"].add_ranges_from_string(hours_string)
            yield Feature(**properties)
