from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class BloomingdalesUSSpider(CrawlSpider, StructuredDataSpider):
    name = "bloomingdales_us"
    item_attributes = {"brand": "Bloomingdale's", "brand_wikidata": "Q283383"}
    allowed_domains = ["bloomingdales.com"]
    download_delay = 0.2
    start_urls = ["https://www.bloomingdales.com/stores/browse/"]
    rules = [
        Rule(LinkExtractor(allow=r"/stores/\w{2}/$")),
        Rule(LinkExtractor(allow=r"/stores/\w{2}/[-\w]+/$")),
        Rule(LinkExtractor(allow=r"/stores/\w{2}/[-\w]+/[-\w]+\.html$"), callback="parse_sd"),
    ]
    user_agent = BROWSER_DEFAULT
