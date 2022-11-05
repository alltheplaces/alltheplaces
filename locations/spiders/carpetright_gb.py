from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser


class CarpetrightGBSpider(CrawlSpider):
    name = "carpetright_gb"
    item_attributes = {"brand": "carpetright", "brand_wikidata": "Q5045782"}
    allowed_domains = ["carpetright.co.uk"]
    start_urls = ["https://www.carpetright.co.uk/store/near-me"]
    rules = [Rule(LinkExtractor(allow="/store/"), callback="parse", follow=True)]
    download_delay = 0.5

    def parse(self, response):
        MicrodataParser.convert_to_json_ld(response.selector)
        item = LinkedDataParser.parse(response, "HomeGoodsStore")
        if item:
            yield item
