import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider

from locations.structured_data_spider import StructuredDataSpider


class MitraNLSpider(CrawlSpider, StructuredDataSpider):
    name = "mitra_nl"
    item_attributes = {"brand": "Mitra", "brand_wikidata": "Q109186241"}
    allowed_domains = ["www.mitra.nl"]
    link_extractor = LinkExtractor(allow="/winkels/")
    wanted_types = [
        "LiquorStore"
    ]
    drop_attributes = {"image"}

    def start_requests(self):
        yield scrapy.Request("https://www.mitra.nl/winkels/", callback=self.parse)

    def parse(self, response):
        links = self.link_extractor.extract_links(response)
        for link in links:
            yield scrapy.Request(link.url, callback=self.parse_sd)

