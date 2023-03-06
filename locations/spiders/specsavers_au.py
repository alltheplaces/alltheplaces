from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class SpecsaversAUSpider(CrawlSpider, StructuredDataSpider):
    name = "specsavers_au"
    item_attributes = {"brand": "Specsavers", "brand_wikidata": "Q2000610"}
    start_urls = ["https://www.specsavers.com.au/stores/full-store-list"]
    rules = [
        Rule(
            LinkExtractor(allow=r"^https:\/\/www\.specsavers\.com\.au\/stores\/(.(?!-hearing))+$"), callback="parse_sd"
        )
    ]
    wanted_types = ["Optician"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item.pop("image")
        item.pop("facebook")
        yield item
