from chompjs import parse_js_object
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.dict_parser import DictParser

HAMLEYS_SHARED_ATTRIBUTES = {"brand": "Hamleys", "brand_wikidata": "Q60299"}


class HamleysSpider(CrawlSpider):
    name = "hamleys"
    allowed_domains = ["www.hamleys.com"]
    start_urls = [
        "https://www.hamleys.com/our-stores",
        "https://www.hamleys.com/our-stores-europe",
    ]
    # TODO: global stores: https://www.hamleys.com/our-stores-global but only addresses and no other info
    item_attributes = HAMLEYS_SHARED_ATTRIBUTES
    rules = [Rule(LinkExtractor(allow="/stores/"), callback="parse")]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        if location_js := response.xpath("//div/@data-locations").get():
            location = parse_js_object(location_js)[0]
        else:
            return
        item = DictParser.parse(location)
        item["branch"] = item.pop("name")
        item["street_address"] = item.pop("addr_full")
        item["website"] = response.url
        item["ref"] = item["website"]
        item["image"] = location.xpath(
            './/div[@class="store-main-banner"]/figure/img[@data-element="mobile_image"]/@src'
        ).get()

        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(response.xpath('string(.//ul[@class="opening-hours"])').get())

        yield item
