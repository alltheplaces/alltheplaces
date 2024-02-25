from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class ObiDESpider(CrawlSpider, StructuredDataSpider):
    name = "obi_de"
    item_attributes = {"brand": "OBI", "brand_wikidata": "Q300518"}
    allowed_domains = ["www.obi.de"]
    start_urls = ["https://www.obi.de/markt/index.html"]
    rules = [Rule(LinkExtractor(allow="https://www.obi.de/markt/.*"), callback="parse_sd")]
    download_delay = 0.5

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["website"] = response.url
        yield item
