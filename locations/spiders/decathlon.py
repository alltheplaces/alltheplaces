import json

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.dict_parser import DictParser


class Decathlon(CrawlSpider):
    name = "decathlon"
    item_attributes = {"brand": "Decathlon", "brand_wikidata": "Q509349"}
    start_urls = [
        "https://www.decathlon.be/nl/store-locator",
        "https://www.decathlon.ch/fr/store-locator",
        "https://www.decathlon.cz/store-locator",
        "https://www.decathlon.co.uk/store-locator",
        "https://www.decathlon.de/store-locator",
        "https://www.decathlon.es/es/store-locator",
        "https://www.decathlon.com.hk/en/store-locator",
        "https://www.decathlon.it/store-locator",
        "https://www.decathlon.fr/store-locator",
        "https://www.decathlon.hu/store-locator",
        "https://www.decathlon.nl/store-locator",
        "https://www.decathlon.pl/store-locator",
        "https://www.decathlon.pt/store-locator",
        "https://www.decathlon.ro/store-locator",
        "https://www.decathlon.com.tr/store-locator",
        # TODO: more domains no doubt
    ]
    rules = [Rule(LinkExtractor(allow="/store-view/"), callback="parse", follow=False)]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    download_delay = 0.5

    def parse(self, response):
        if script := response.xpath('//script[@id="__dkt"]/text()').get():
            store = json.loads(script)
            details = DictParser.get_nested_key(store, "items")
            item = DictParser.parse(details[0])
            item["website"] = response.url
            yield item
