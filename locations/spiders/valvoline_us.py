from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class ValvolineUSSpider(CrawlSpider, StructuredDataSpider):
    name = "valvoline_us"
    item_attributes = {"brand": "Valvoline", "brand_wikidata": "Q7912852"}
    drop_attributes = {"name"}
    start_urls = ["https://store.vioc.com/"]
    rules = [
        Rule(LinkExtractor(r"https://store.vioc.com/\w\w/$")),
        Rule(LinkExtractor(r"https://store.vioc.com/\w\w/[^/]+/$")),
        Rule(LinkExtractor(r"https://store.vioc.com/\w\w/[^/]+/oil-change-([\w\d]+)\.html$"), "parse"),
    ]
    wanted_types = ["AutoRepair"]
