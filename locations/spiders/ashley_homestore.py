from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.linked_data_parser import LinkedDataParser


class AshleyHomestoreSpider(CrawlSpider):
    name = "ashley_homestore"
    item_attributes = {"brand": "Ashley HomeStore", "brand_wikidata": "Q4805437"}
    start_urls = ["https://stores.ashleyhomestore.ca/store/"]
    allowed_domains = ["stores.ashleyhomestore.ca"]
    rules = [Rule(LinkExtractor(allow="/store/"), callback="parse_store", follow=True)]

    def parse_store(self, response):
        item = LinkedDataParser.parse(response, "FurnitureStore")
        if item:
            item["ref"] = response.url
            yield item
