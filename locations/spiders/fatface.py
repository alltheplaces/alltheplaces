from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser


class FatFaceSpider(CrawlSpider):
    name = "fatface"
    item_attributes = {"brand": "FATFACE", "brand_wikidata": "Q5437186"}
    allowed_domains = ["fatface.com"]
    start_urls = ["https://www.fatface.com/stores"]
    rules = [Rule(LinkExtractor(allow="/store/"), callback="parse", follow=False)]
    download_delay = 0.5

    def parse(self, response):
        MicrodataParser.convert_to_json_ld(response.selector)
        item = LinkedDataParser.parse(response, "Store")
        if item:
            item["ref"] = response.url
            item["lat"] = response.xpath("//@data-latitude").get()
            item["lon"] = response.xpath("//@data-longitude").get()
            yield item
