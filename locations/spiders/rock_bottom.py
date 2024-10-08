import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories
from locations.items import Feature


class RockBottomSpider(CrawlSpider):
    name = "rock_bottom"
    item_attributes = {"brand": "Rock Bottom", "brand_wikidata": "Q73504866", "extras": Categories.RESTAURANT.value}
    allowed_domains = ["rockbottom.com"]
    download_delay = 0.5
    start_urls = ["https://www.rockbottom.com/locations"]
    rules = [Rule(LinkExtractor(allow=r"/locations/[a-z-]+"), callback="parse")]

    def parse(self, response):
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["addr_full"] = response.xpath('//*[@class="location-address"]/a/text()').get()
        item["phone"] = response.xpath('//*[@class="location-address"]/a[2]/text()').get()
        if location := response.xpath('//section[@id="mapDetailDiv"]/div/a/img/@src').get():
            if match := re.search(r"\(?(-?[0-9]+.[0-9]+)\,([0-9]+.[0-9]+)\/", location):
                item["lon"] = match.group(1)
                item["lat"] = match.group(2)
        yield item
