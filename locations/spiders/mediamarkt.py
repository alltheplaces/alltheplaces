from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class MediaMarktSpider(CrawlSpider, StructuredDataSpider):
    name = "media_markt"
    item_attributes = {"brand": "MediaMarkt", "brand_wikidata": "Q2381223"}
    start_urls = ["https://www.mediamarkt.de/de/store/store-finder"]
    rules = [Rule(LinkExtractor(allow=r"https://www.mediamarkt.de/de/store/"), callback="parse_sd")]
