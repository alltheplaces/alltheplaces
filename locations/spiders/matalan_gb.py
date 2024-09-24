import json

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.dict_parser import DictParser
from locations.structured_data_spider import StructuredDataSpider


class MatalanGBSpider(CrawlSpider, StructuredDataSpider):
    name = "matalan_gb"
    item_attributes = {"brand": "Matalan", "brand_wikidata": "Q12061509"}
    allowed_domains = ["www.matalan.co.uk"]
    start_urls = ["https://www.matalan.co.uk/stores/uk"]
    rules = [
        Rule(LinkExtractor(allow=r"^https://www.matalan.co.uk/stores/uk/[-\w]+$")),
        Rule(LinkExtractor(allow=r"^https://www.matalan.co.uk/stores/uk/[-\w]+/[-\w]+$")),
        Rule(LinkExtractor(allow=r"^https://www.matalan.co.uk/store/[-\/\w]+$"), "parse_sd"),
    ]
    time_format = "%H:%M:%S"

    def post_process_item(self, item, response, ld_data, **kwargs):
        storedata = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        store = json.loads(storedata)["props"]["pageProps"]["store"]
        item = DictParser.parse(store)
        yield item
