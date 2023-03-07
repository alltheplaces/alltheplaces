from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class StroiliOroITSpider(CrawlSpider, StructuredDataSpider):
    name = "stroili_oro_it"
    item_attributes = {"brand_wikidata": "Q106611306"}
    start_urls = ["https://www.stroilioro.com/it_IT/gioiellerie-stroili/tutti-negozi/"]
    rules = [
        Rule(LinkExtractor(allow=r"\?cityId=")),
        Rule(LinkExtractor(allow=r"\?storeID=\d+$"), callback="parse_sd"),
    ]
    wanted_types = ["JewelryStore"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["website"] = response.url
        item["image"] = None

        yield item
