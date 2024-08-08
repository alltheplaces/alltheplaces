from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class TigotaITSpider(CrawlSpider, StructuredDataSpider):
    name = "tigota_it"
    item_attributes = {"brand": "Tigotà", "brand_wikidata": "Q107464330"}
    allowed_domains = ["negozi.tigota.it"]
    start_urls = ["https://negozi.tigota.it/"]
    rules = [
        Rule(LinkExtractor(r"\.it/[^/]+-\d+$")),
        Rule(LinkExtractor(r"\.it/\d+-.+$"), "parse"),
    ]
    wanted_types = ["Store"]
