import json

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider
from locations.linked_data_parser import LinkedDataParser

class MatalanGBSpider(CrawlSpider,StructuredDataSpider):
    name = "matalan_gb"
    item_attributes = {"brand": "Matalan", "brand_wikidata": "Q12061509"}
    allowed_domains = ["www.matalan.co.uk"]
    start_urls = ['https://www.matalan.co.uk/stores/uk']
    rules = [
        Rule(LinkExtractor(allow=r"^https://www.matalan.co.uk/stores/uk/[-\w]+$")),
        Rule(LinkExtractor(allow=r"^https://www.matalan.co.uk/stores/uk/[-\w]+/[-\w]+$")),
        Rule(LinkExtractor(allow=r"^https://www.matalan.co.uk/store/[-\/\w]+$"), "parse_sd"),
    ]
    download_delay = 0.5
    time_format = "%H:%M:%S"

    def post_process_item(self, item, response, ld_data, **kwargs):
        ld = response.xpath('//script[@type="application/ld+json"]/text()').get()
        ld_item = json.loads(ld)

        item = LinkedDataParser.parse_ld(ld_item,time_format="%H:%M:%S")
        item["ref"]=ld_item["url"]
        yield item
