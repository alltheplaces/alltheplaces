from scrapy.spiders import Spider

from locations.google_url import extract_google_position
from locations.items import Feature
from locations.spiders.taco_bell import TACO_BELL_SHARED_ATTRIBUTES


class TacoBellNLSpider(Spider):
    name = "taco_bell_nl"
    item_attributes = TACO_BELL_SHARED_ATTRIBUTES
    start_urls = ["https://tacobell.nl/en/locations/"]
    no_refs = True

    def parse(self, response, **kwargs):
        for restaurant in response.xpath(r'//*[@class="find-Us-Branches"]'):
            item = Feature()
            item["name"] = restaurant.xpath('.//*[@class = "storename"]/text()').get()
            item["addr_full"] = restaurant.xpath('.//*[@class = "findus_addr"]/text()').get()
            item["phone"] = restaurant.xpath('.//*[@class = "store-mobile"]//text()').get()
            item["website"] = "https://tacobell.nl/"
            extract_google_position(item, response)
            yield item
