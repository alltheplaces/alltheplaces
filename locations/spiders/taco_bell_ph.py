from scrapy.spiders import Spider

from locations.google_url import extract_google_position
from locations.items import Feature
from locations.spiders.taco_bell_us import TACO_BELL_SHARED_ATTRIBUTES


class TacoBellPHSpider(Spider):
    name = "taco_bell_ph"
    item_attributes = TACO_BELL_SHARED_ATTRIBUTES
    start_urls = ["https://tacobell.com.ph/locations/"]
    no_refs = True

    def parse(self, response, **kwargs):
        for location in response.xpath('//*[@class="find-Us-Branches"]'):
            item = Feature()
            item["name"] = location.xpath('.//*[@class = "storename"]/text()').get()
            item["addr_full"] = location.xpath('.//*[@class = "findus_addr"]/text()').get()
            item["phone"] = location.xpath('.//*[@class = "store-mobile"]//text()').get()
            extract_google_position(item, location)
            yield item
