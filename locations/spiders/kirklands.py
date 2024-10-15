from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class KirklandsSpider(CrawlSpider, StructuredDataSpider):
    name = "kirklands"
    item_attributes = {
        "brand": "Kirkland's",
        "brand_wikidata": "Q6415714",
    }
    start_urls = ["https://www.kirklands.com/custserv/locate_store.cmd"]
    rules = [Rule(LinkExtractor(allow="/store.jsp?"), callback="parse_sd")]
    requires_proxy = True
