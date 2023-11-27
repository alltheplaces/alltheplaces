import scrapy
from scrapy.selector import Selector

from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT


class PricelineAUSpider(scrapy.Spider):
    name = "priceline_au"
    allowed_domains = [""]
    item_attributes = {"brand": "Priceline", "brand_wikidata": "Q7242652"}
    start_urls = ("https://www.priceline.com.au/ustorelocator/location/map/?ajax=1&page=1",)
    user_agent = BROWSER_DEFAULT

    def parse(self, response):
        data = response.json()
        for store in data["markers"]:
            item = DictParser.parse(store)
            yield item
        next_page_html = data["pager_html"]
        next_url = Selector(text=next_page_html).xpath("//a[contains(@class, 'next')]/@href").get()
        if next_url is not None:
            yield scrapy.Request(url=next_url, callback=self.parse)
