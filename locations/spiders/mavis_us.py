from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class MavisUSSpider(CrawlSpider, StructuredDataSpider):
    name = "mavis_us"
    item_attributes = {"brand_wikidata": "Q65058420"}
    start_urls = ["https://www.mavis.com/locations/all-stores/"]
    rules = [
        Rule(
            LinkExtractor(allow=r"/locations/[^/]+/$", restrict_xpaths=['//a[starts-with(text(), "Mavis")]']),
            callback="parse",
        )
    ]
    wanted_types = ["Store"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = None
        item["addr_full"] = item.pop("street_address")

        yield item
