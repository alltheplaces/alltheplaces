import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class LaHalleFRSpider(CrawlSpider, StructuredDataSpider):
    name = "la_halle_fr"
    item_attributes = {"brand": "La Halle", "brand_wikidata": "Q100728296"}
    start_urls = ["https://www.lahalle.com/magasins"]
    rules = [
        Rule(LinkExtractor(restrict_xpaths='//div[@id="store-locator-home-departements"]')),
        Rule(LinkExtractor(restrict_xpaths='//a[@class="store-details-link"]'), callback="parse_sd"),
    ]
    wanted_types = ["LocalBusiness", "ClothingStore"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if script := response.xpath('//script[contains(text(), "env_template")]/text()').get():
            if lat := re.search(r'\\"store_latitude\\":\\"(-?\d+\.\d+)\\",', script):
                item["lat"] = lat.group(1)
            if lon := re.search(r'\\"store_longitude\\":\\"(-?\d+\.\d+)\\",', script):
                item["lon"] = lon.group(1)
        yield item
