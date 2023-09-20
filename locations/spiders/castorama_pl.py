from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class CastoramaPLSpider(CrawlSpider, StructuredDataSpider):
    name = "castorama_pl"
    item_attributes = {"brand": "Castorama", "brand_wikidata": "Q966971"}
    start_urls = ["https://www.castorama.pl/informacje/sklepy"]
    rules = [Rule(LinkExtractor(allow=[r"/sklepy/[-\w]+.html$"]), callback="parse_sd")]
    wanted_types = ["HardwareStore"]
    time_format = "%H:%M:%S Europe/Warsaw"
