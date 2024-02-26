from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class MacysBackstageSpider(CrawlSpider, StructuredDataSpider):
    name = "macys_backstage"
    item_attributes = {"brand": "Macy's Backstage", "brand_wikidata": "Q122914589"}
    start_urls = ["https://www.macys.com/stores/backstage/browse/"]
    rules = [
        Rule(LinkExtractor(r"/stores/backstage/\w\w/$")),
        Rule(LinkExtractor(r"/stores/backstage/\w\w/[^/]+/$")),
        Rule(LinkExtractor(r"/stores/backstage/\w\w/[^/]+/[^/]+\_(\d+b).html$"), "parse"),
    ]
    wanted_types = ["Store"]
    user_agent = BROWSER_DEFAULT

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = None
        yield item
