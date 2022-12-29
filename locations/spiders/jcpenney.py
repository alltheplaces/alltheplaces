from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.user_agents import BROSWER_DEFAULT
from locations.structured_data_spider import StructuredDataSpider


class JCPenneySpider(CrawlSpider, StructuredDataSpider):
    name = "jcpenney"
    item_attributes = {"brand": "JCPenney", "brand_wikidata": "Q920037"}
    allowed_domains = ["jcpenney.com"]
    start_urls = ["https://jcpenney.com/locations/"]
    rules = [
        Rule(LinkExtractor(allow=r"/locations/[-\w]{2}$"), follow=True),
        Rule(LinkExtractor(allow=r"/locations/[-\w]{2}/[-\w]+/[-\w]+.html$"), follow=True, callback="parse_sd"),
    ]
    user_agent = BROSWER_DEFAULT
    wanted_types = ["DepartmentStore"]
