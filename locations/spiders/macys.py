from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class MacysSpider(CrawlSpider, StructuredDataSpider):
    name = "macys"
    item_attributes = {"brand": "Macy's", "brand_wikidata": "Q629269"}
    allowed_domains = ["macys.com"]
    start_urls = ["https://www.macys.com/stores/browse/"]
    rules = [
        Rule(LinkExtractor(r"/stores/\w\w/$")),
        Rule(LinkExtractor(r"/stores/\w\w/[^/]+/$")),
        Rule(LinkExtractor(r"/stores/\w\w/[^/]+/[^/]+\_(\d+).html$"), "parse"),
    ]
    wanted_types = ["Store"]
    user_agent = BROWSER_DEFAULT

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = None
        yield item
