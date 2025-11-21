from typing import AsyncIterator

from scrapy.http import Request
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider

from locations.structured_data_spider import StructuredDataSpider


class MitraNLSpider(CrawlSpider, StructuredDataSpider):
    name = "mitra_nl"
    item_attributes = {"brand": "Mitra", "brand_wikidata": "Q109186241"}
    allowed_domains = ["www.mitra.nl"]
    link_extractor = LinkExtractor(allow="/winkels/")
    wanted_types = ["LiquorStore"]
    drop_attributes = {"image"}

    async def start(self) -> AsyncIterator[Request]:
        yield Request("https://www.mitra.nl/winkels/", callback=self.parse)

    def parse(self, response):
        links = self.link_extractor.extract_links(response)
        for link in links:
            yield Request(link.url, callback=self.parse_sd)
